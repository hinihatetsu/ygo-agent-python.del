import enum

class Player(enum.IntEnum):
    ME       = 0
    OPPONENT = 1
    NONE     =-1



class Phase(enum.IntEnum):
    DRAW         = 0x1
    STANBY       = 0x2
    MAIN1        = 0x4
    BATTLE_START = 0x8
    BATTLE_STEP  = 0x10
    DAMAGE_STEP  = 0x20
    DAMAGE_CALC  = 0x40
    BATTLE       = 0x80
    MAIN2        = 0x100
    END          = 0x200

    

class CardLocation(enum.IntEnum):
    DECK          = 0x1
    HAND          = 0x2
    MONSTER_ZONE  = 0x4
    SPELL_ZONE    = 0x8
    GRAVE         = 0x10
    BANISHED      = 0x20
    EXTRADECK     = 0x40
    OVERRAY       = 0x80
    ONFIELD = MONSTER_ZONE | SPELL_ZONE
    FSPELL_ZONE   = 0x100
    PENDULUM_ZONE = 0x200
    



class CardType(enum.IntEnum):
    MONSTER     = 0x1
    SPELL       = 0x2
    TRAP        = 0x4
    NORMAL      = 0x10
    EFFECT      = 0x20
    FUSION      = 0x40
    RITUAL      = 0x80
    TRAPMONSTER = 0x100
    SPIRIT      = 0x200
    UNION       = 0x400
    GEMINI      = 0x800
    TUNER       = 0x1000
    SYNCHRO     = 0x2000
    TOKEN       = 0x4000
    QUICKPLAY   = 0x10000
    CONTINUOUS  = 0x20000
    EQUIP       = 0x40000
    FIELD       = 0x80000
    COUNTER     = 0x100000
    FLIP        = 0x200000
    TOON        = 0x400000
    XYZ         = 0x800000
    PENDULUM    = 0x1000000
    SPSUMMON    = 0x2000000
    LINK        = 0x4000000



class Attribute(enum.IntEnum):
    EARTH  = 0x01
    WATER  = 0x02
    FIRE   = 0x04
    WIND   = 0x08
    LIGHT  = 0x10
    DARK   = 0x20
    DIVINE = 0x40



class Race(enum.IntEnum):
    WARRIOR      = 0x1
    SPELLCASTER  = 0x2
    FAIRY        = 0x4
    FIEND        = 0x8
    ZOMBIE       = 0x10
    MACHINE      = 0x20
    AQUA         = 0x40
    PYRO         = 0x80
    ROCK         = 0x100
    WINGEDBEAST  = 0x200
    PLANT        = 0x400
    INSECT       = 0x800
    THUNDER      = 0x1000
    DRAGON       = 0x2000
    BEAST        = 0x4000
    BEASTWARRIOR = 0x8000
    DINOSAUR     = 0x10000
    FISH         = 0x20000
    SEASERPENT   = 0x40000
    REPTILE      = 0x80000
    PSYCHIC      = 0x100000
    DIVINE       = 0x200000
    CREATORGOD   = 0x400000
    WYRM         = 0x800000
    CYBERSE      = 0x1000000



class CardPosition(enum.IntEnum):
    _                = 0x0
    FASEUP_ATTACK    = 0x1
    FASEDOWN_ATTACK  = 0x2
    FASEUP_DEFENCE   = 0x4
    FASEDOWN_DEFENCE = 0x8
    FACEUP = FASEUP_ATTACK | FASEUP_DEFENCE 
    FACEDOWN = FASEDOWN_ATTACK | FASEDOWN_DEFENCE
    ATTACK = FASEUP_ATTACK | FASEDOWN_ATTACK
    DEFENCE = FASEUP_DEFENCE | FASEDOWN_DEFENCE



class Query(enum.IntEnum):
    ID           = 0x1
    POSITION     = 0x2
    ALIAS        = 0x4
    TYPE         = 0x8
    LEVEL        = 0x10
    RANK         = 0x20
    ATTRIBUTE    = 0x40
    RACE         = 0x80
    ATTACK       = 0x100
    DEFENCE      = 0x200
    BASE_ATTACK  = 0x400
    BASE_DEFENCE = 0x800
    REASON       = 0x1000
    REASON_CARD  = 0x2000
    EQUIP_CARD   = 0x4000
    TARGET_CARD  = 0x8000
    OVERLAY_CARD = 0x10000
    COUNTERS     = 0x20000
    CONTROLLER   = 0x40000
    STATUS       = 0x80000
    LSCALE       = 0x200000
    RSCALE       = 0x400000
    LINK         = 0x800000
    IS_HIDDEN    = 0x1000000
    COVER        = 0x2000000
    END          = 0x80000000


