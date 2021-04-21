import os
import tempfile
from typing import List

import numpy as np
import tensorflow as tf
import reverb

from tf_agents.agents.ddpg import critic_network
from tf_agents.agents.sac.sac_agent import SacAgent
from tf_agents.agents.sac.tanh_normal_projection_network import TanhNormalProjectionNetwork
from tf_agents.metrics import py_metrics
from tf_agents.networks import actor_distribution_network
from tf_agents.policies.py_tf_eager_policy import PyTFEagerPolicy
from tf_agents.policies import random_py_policy
from tf_agents.replay_buffers.reverb_replay_buffer import ReverbReplayBuffer
from tf_agents.replay_buffers.reverb_utils import ReverbAddTrajectoryObserver
from tf_agents.train import actor, learner, triggers
from tf_agents.train.utils import train_utils, spec_utils

from pyYGOenv import YGOEnv

tempdir: str = tempfile.gettempdir()

_initial_collect_episodes = 10 # @param {type:"integer"}
_collect_steps_per_iteration = 1 # @param {type:"integer"}
_replay_buffer_capacity = 10000 # @param {type:"integer"}

_batch_size = 256 # @param {type:"integer"}

_log_interval = 500 # @param {type:"integer"}

_num_eval_episodes = 5 # @param {type:"integer"}
_eval_interval = 10000 # @param {type:"integer"}

_policy_save_interval = 5000 # @param {type:"integer"}


class DuelAgent:
    """ Duel agent with SAC algorithm """
    def __init__(self, collect_env: YGOEnv, eval_env: YGOEnv) -> None:
        self._collect_env: YGOEnv = collect_env
        self._eval_env: YGOEnv = eval_env
        
        # hyper parameters
        self._actor_fc_layer_params: List[int] = [512, 256]
        self._critic_joint_fc_layer_params: List[int] = [512, 256]
        self._critic_learning_rate: float = 3e-4
        self._actor_learning_rate: float = 3e-4
        self._alpha_learning_rate: float = 3e-4
        self._target_update_tau: float = 0.005
        self._target_update_period: int = 1
        self._gamma: float = 0.99
        self._reward_scale_factor: float = 1.0
        table_name: str = 'uniform_table'

        # Agent
        self._train_step = train_utils.create_train_step()
        self._agent: SacAgent = self._create_agent()
        # reverb
        self._reverb_server: reverb.Server = self._create_reverb_server(table_name)
        self._reverb_replay: ReverbReplayBuffer = self._create_replay_buffer(table_name)
        # policy
        self._eval_policy: PyTFEagerPolicy = PyTFEagerPolicy(self._agent.policy, use_tf_function=True)
        self._collect_policy: PyTFEagerPolicy = PyTFEagerPolicy(self._agent.collect_policy, use_tf_function=True)
        # actor
        self._rb_observer: ReverbAddTrajectoryObserver = self._create_rb_observer(table_name)
        self._collect_actor: actor.Actor = self._create_collect_actor()
        self._eval_actor: actor.Actor = self._create_eval_actor()
        # learner
        self._agent_learner: learner.Learner = self._create_agent_learner()


    def _create_agent(self) -> SacAgent:
        observation_spec, action_spec, time_step_spec = spec_utils.get_tensor_specs(self._collect_env)

        critic_net = critic_network.CriticNetwork(
            (observation_spec, action_spec),
            observation_fc_layer_params=None,
            action_fc_layer_params=None,
            joint_fc_layer_params=self._critic_joint_fc_layer_params,
        )

        actor_net = actor_distribution_network.ActorDistributionNetwork(
            observation_spec,
            action_spec,
            fc_layer_params=self._actor_fc_layer_params,
            continuous_projection_net=TanhNormalProjectionNetwork
        )

        tf_agent = SacAgent(
            time_step_spec,
            action_spec,
            actor_network=actor_net,
            critic_network=critic_net,
            actor_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=self._actor_learning_rate),
            critic_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=self._critic_learning_rate),
            alpha_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=self._alpha_learning_rate),
            target_update_tau=self._target_update_tau,
            target_update_period=self._target_update_period,
            td_errors_loss_fn=tf.math.squared_difference,
            gamma=self._gamma,
            reward_scale_factor=self._reward_scale_factor,
            train_step_counter=self._train_step
        )
        tf_agent.initialize()

        return tf_agent


    def _create_reverb_server(self, table_name: str) -> reverb.Server:
        table = reverb.Table(
            table_name,
            max_size=_replay_buffer_capacity,
            sampler=reverb.selectors.Uniform(),
            remover=reverb.selectors.Fifo(),
            rate_limiter=reverb.rate_limiters.MinSize(1)
        )
        return reverb.Server([table])

    
    def _create_replay_buffer(self, table_name: str) -> ReverbReplayBuffer:
        return ReverbReplayBuffer(
            self._agent.collect_data_spec,
            sequence_length=2,
            table_name=table_name,
            local_server=self._reverb_server
        )


    def _create_rb_observer(self, table_name: str) -> ReverbAddTrajectoryObserver:
        return ReverbAddTrajectoryObserver(
            self._reverb_replay.py_client,
            table_name,
            sequence_length=2,
            stride_length=1
        )


    def _create_collect_actor(self) -> actor.Actor:

        initial_collect_actor = actor.Actor(
            self._collect_env,
            random_py_policy.RandomPyPolicy(self._collect_env.time_step_spec(), self._collect_env.action_spec()),
            self._train_step,
            episodes_per_run=_initial_collect_episodes,
            observers=[self._rb_observer]
        )
        initial_collect_actor.run()
        

        return actor.Actor(
            self._collect_env,
            self._collect_policy,
            self._train_step,
            episodes_per_run=1,
            metrics=actor.collect_metrics(10),
            summary_dir=os.path.join(tempdir, learner.TRAIN_DIR),
            observers=[self._rb_observer, py_metrics.EnvironmentSteps()]
        )

    
    def _create_eval_actor(self) -> actor.Actor:
        return actor.Actor(
            self._eval_env,
            self._eval_policy,
            self._train_step,
            episodes_per_run=_num_eval_episodes,
            metrics=actor.eval_metrics(_num_eval_episodes),
            summary_dir=os.path.join(tempdir, 'eval')
        )
    

    def _create_agent_learner(self) -> learner.Learner:
        learning_triggers = [
            triggers.PolicySavedModelTrigger(
                os.path.join(tempdir, learner.POLICY_SAVED_MODEL_DIR),
                self._agent,
                self._train_step,
                interval=_policy_save_interval
            ),
            triggers.StepPerSecondLogTrigger(self._train_step, interval=1000)
        ]

        return learner.Learner(
            tempdir,
            self._train_step,
            self._agent,
            lambda: self._reverb_replay.as_dataset(sample_batch_size=_batch_size, num_steps=2).prefetch(50),
            triggers=learning_triggers
        )


    def _get_eval_metrics(self) -> dict:
        self._eval_actor.run()
        results = {}
        for metric in self._eval_actor.metrics:
            results[metric.name] = metric.result()
        return results

    
    def _log_eval_metrics(self, step: int, metrics: dict) -> None:
        eval_results = ', '.join(f'{name} = {result:.6f}' for name, result in metrics.items())
        print(f'step = {step}: {eval_results}')

    
    def train(self, iterations: int) -> None:
        self._agent.train_step_counter.assign(0)

        returns = [self._get_eval_metrics()['AverageReturn']]

        for _ in range(iterations):
            self._collect_actor.run()
            loss_info = self._agent_learner.run(num_iterations=1)

            step = int(self._agent_learner.train_step_numpy)

            if step % _eval_interval == 0:
                metrics = self._get_eval_metrics()
                self._log_eval_metrics(step, metrics)
                returns.append(metrics['AverageReturn'])

            if step % _log_interval == 0:
                print(f'step = {step}: loss = {loss_info.loss.numpy()}')

        #self._rb_observer.close()
        #self._reverb_server.stop()