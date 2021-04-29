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
        self._actor_fc_layer_params: List[int] = [256, 256]
        self._critic_joint_fc_layer_params: List[int] = [256, 256]
        self._critic_learning_rate: float = 3e-4
        self._actor_learning_rate: float = 3e-4
        self._alpha_learning_rate: float = 3e-4
        self._target_update_tau: float = 0.005
        self._target_update_period: int = 1
        self._gamma: float = 0.99
        self._reward_scale_factor: float = 1.0
        table_name: str = 'uniform_table'

        # Agent
        train_step = train_utils.create_train_step()
        self._agent: SacAgent = _create_agent(self, train_step)
        # reverb
        self._reverb_server: reverb.Server = _create_reverb_server(table_name)
        self._reverb_replay_buffer: ReverbReplayBuffer = _create_replay_buffer(self._agent.collect_data_spec, self._reverb_server, table_name)
        # policy
        self._eval_policy: PyTFEagerPolicy = PyTFEagerPolicy(self._agent.policy, use_tf_function=True)
        self._collect_policy: PyTFEagerPolicy = PyTFEagerPolicy(self._agent.collect_policy, use_tf_function=True)
        # actor
        self._rb_observer: ReverbAddTrajectoryObserver = _create_rb_observer(self._reverb_replay_buffer, table_name)
        self._collect_actor: actor.Actor = _create_collect_actor(self._collect_env, self._collect_policy, train_step, self._rb_observer)
        self._eval_actor: actor.Actor = _create_eval_actor(self._eval_env, self._eval_policy, train_step)
        # learner
        self._agent_learner: learner.Learner = _create_agent_learner(self._agent, train_step, self._reverb_replay_buffer)


    def train(self, iterations: int) -> None:
        self._agent.train_step_counter.assign(0)

        returns = [_get_eval_metrics(self._eval_actor)['AverageReturn']]

        for _ in range(iterations):
            self._collect_actor.run()
            loss_info = self._agent_learner.run(iterations=1)

            step = int(self._agent_learner.train_step_numpy)

            if step % _eval_interval == 0:
                metrics = _get_eval_metrics(self._eval_actor)
                _log_eval_metrics(step, metrics)
                returns.append(metrics['AverageReturn'])

            if step % _log_interval == 0:
                print(f'step = {step}: loss = {loss_info.loss.numpy()}')

        #self._rb_observer.close()
        #self._reverb_server.stop()


def _create_agent(agent: DuelAgent, train_step) -> SacAgent:
    observation_spec, action_spec, time_step_spec = spec_utils.get_tensor_specs(agent._collect_env)

    critic_net = critic_network.CriticNetwork(
        (observation_spec, action_spec),
        observation_fc_layer_params=None,
        action_fc_layer_params=None,
        joint_fc_layer_params=agent._critic_joint_fc_layer_params,
    )

    actor_net = actor_distribution_network.ActorDistributionNetwork(
        observation_spec,
        action_spec,
        fc_layer_params=agent._actor_fc_layer_params,
        continuous_projection_net=TanhNormalProjectionNetwork
    )

    tf_agent = SacAgent(
        time_step_spec,
        action_spec,
        actor_network=actor_net,
        critic_network=critic_net,
        actor_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=agent._actor_learning_rate),
        critic_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=agent._critic_learning_rate),
        alpha_optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=agent._alpha_learning_rate),
        target_update_tau=agent._target_update_tau,
        target_update_period=agent._target_update_period,
        td_errors_loss_fn=tf.math.squared_difference,
        gamma=agent._gamma,
        reward_scale_factor=agent._reward_scale_factor,
        train_step_counter=train_step
    )
    tf_agent.initialize()

    return tf_agent


def _create_reverb_server(table_name: str) -> reverb.Server:
    table = reverb.Table(
        table_name,
        max_size=_replay_buffer_capacity,
        sampler=reverb.selectors.Uniform(),
        remover=reverb.selectors.Fifo(),
        rate_limiter=reverb.rate_limiters.MinSize(1)
    )
    return reverb.Server([table])


def _create_replay_buffer(collect_data_spec, reverb_server: reverb.Server, table_name: str) -> ReverbReplayBuffer:
    return ReverbReplayBuffer(
        collect_data_spec,
        sequence_length=2,
        table_name=table_name,
        local_server=reverb_server
    )


def _create_rb_observer(reverb_replay_buffer: ReverbReplayBuffer, table_name: str) -> ReverbAddTrajectoryObserver:
    return ReverbAddTrajectoryObserver(
        reverb_replay_buffer.py_client,
        table_name,
        sequence_length=2,
        stride_length=1
    )


def _create_collect_actor(collect_env: YGOEnv, collect_policy: PyTFEagerPolicy, train_step, rb_observer: ReverbAddTrajectoryObserver) -> actor.Actor:

    initial_collect_actor = actor.Actor(
        collect_env,
        random_py_policy.RandomPyPolicy(collect_env.time_step_spec(), collect_env.action_spec()),
        train_step,
        episodes_per_run=_initial_collect_episodes,
        observers=[rb_observer]
    )
    initial_collect_actor.run()
    

    return actor.Actor(
        collect_env,
        collect_policy,
        train_step,
        episodes_per_run=1,
        metrics=actor.collect_metrics(10),
        summary_dir=os.path.join(tempdir, learner.TRAIN_DIR),
        observers=[rb_observer, py_metrics.EnvironmentSteps()]
    )


def _create_eval_actor(eval_env: YGOEnv, eval_policy: PyTFEagerPolicy, train_step) -> actor.Actor:
    return actor.Actor(
        eval_env,
        eval_policy,
        train_step,
        episodes_per_run=_num_eval_episodes,
        metrics=actor.eval_metrics(_num_eval_episodes),
        summary_dir=os.path.join(tempdir, 'eval')
    )


def _create_agent_learner(tf_agent, train_step, reverb_replay_buffer: ReverbReplayBuffer) -> learner.Learner:
    learning_triggers = [
        triggers.PolicySavedModelTrigger(
            os.path.join(tempdir, learner.POLICY_SAVED_MODEL_DIR),
            tf_agent,
            train_step,
            interval=_policy_save_interval
        ),
        triggers.StepPerSecondLogTrigger(train_step, interval=1000)
    ]

    return learner.Learner(
        tempdir,
        train_step,
        tf_agent,
        lambda: reverb_replay_buffer.as_dataset(sample_batch_size=_batch_size, num_steps=2).prefetch(50),
        triggers=learning_triggers
    )


def _get_eval_metrics(eval_actor: actor.Actor) -> dict:
    eval_actor.run()
    results = {}
    for metric in eval_actor.metrics:
        results[metric.name] = metric.result()
    return results


def _log_eval_metrics(step: int, metrics: dict) -> None:
    eval_results = ', '.join(f'{name} = {result:.6f}' for name, result in metrics.items())
    print(f'step = {step}: {eval_results}')

    