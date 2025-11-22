from re import I
from components import consumable, equippable
from components.ai import BossAI, HostileEnemy, HostileEnemyWithProjectile, RangedEnemy
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)
orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)
orc_archer = Actor(
    char="O",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemyWithProjectile,  # Changed from HostileEnemy
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)
goblin_archer = Actor(
    char="g",
    color=(127, 127, 63),
    name="Goblin Archer",
    ai_cls=RangedEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=8, base_defense=0, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=40),
)
dragon = Actor(
    char= "D",
    color=(200, 7, 82),
    name="Ancient Dragon",
    ai_cls=BossAI,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=4, base_power=8),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=300)
)
demon = Actor(
    char= "&",
    color=(199, 42, 0),
    name="Ancient Dragon",
    ai_cls=BossAI,
    equipment=Equipment(),
    fighter=Fighter(hp=50, base_defense=4, base_power=8),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=320)
)
confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)
fireball_scroll = Item(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)
health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)
strength_potion = Item(
    char="!",
    color=(0, 25, 0),
    name="Strength Potion",
    consumable=consumable.StrengthPotionConsumable(number_of_turns=5, power_boost=3),
)
defense_potion = Item(
    char="!",
    color=(0, 0, 25),
    name="Defense Potion",
    consumable=consumable.DefensePotionConsumable(number_of_turns=7, defense_boost=2),
)
ice_bomb = Item(
    char="*",
    color=(135, 206, 250),
    name="Ice Bomb",
    consumable=consumable.IceBombConsumable(number_of_turns=5, radius=3),
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)
arrow_scroll = Item(
    char="^",
    color=(150, 150, 255),
    name="Arrow Scroll",
    consumable=consumable.DirectionalProjectileConsumable(
        damage=8,
        projectile_range=10,
        symbols=["→", "⇒", "➤"],  # Animated arrow
        projectile_color=(200, 200, 255)
    ),
)
shockwave_scroll = Item(
    char="^",
    color=(100, 200, 255),
    name="Shockwave Scroll",
    consumable=consumable.ShockwaveConsumable(damage=10, radius=4),
)
cross_blast_scroll = Item(
    char="^",
    color=(255, 100, 100),
    name="Cross Blast Scroll",
    consumable=consumable.CrossBlastConsumable(damage=12, projectile_range=5),
)
diagonal_blast_scroll = Item(
    char="^",
    color=(200, 100, 255),
    name="Diagonal Blast Scroll",
    consumable=consumable.DiagonalBlastConsumable(damage=12, projectile_range=5),
)
dagger = Item(
    char="/",
    color=(0, 191, 255),
    name="Dagger",
    equippable=equippable.Dagger())

sword = Item(
    char="/",
    color=(0, 191, 255),
    name="Sword",
    equippable=equippable.Sword())

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
)

chain_mail = Item(
    char="[",
    color=(139, 69, 19),
    name="Chain Mail",
    equippable=equippable.ChainMail()
    )

greatsword = Item(
    char="/",
    color=(255, 50, 50),
    name="Greatsword",
    equippable=equippable.Greatsword(),
)

rapier = Item(
    char="/",
    color=(200, 200, 255),
    name="Rapier",
    equippable=equippable.Rapier(),
)

battle_axe = Item(
    char="/",
    color=(180, 100, 50),
    name="Battle Axe",
    equippable=equippable.BattleAxe(),
)

plate_armor = Item(
    char="[",
    color=(192, 192, 192),
    name="Plate Armor",
    equippable=equippable.PlateArmor(),
)

mage_robe = Item(
    char="[",
    color=(100, 100, 255),
    name="Mage Robe",
    equippable=equippable.MageRobe(),
)

dragon_scale = Item(
    char="[",
    color=(255, 50, 50),
    name="Dragon Scale Armor",
    equippable=equippable.DragonScale(),
)
