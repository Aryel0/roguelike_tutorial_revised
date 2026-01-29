from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from components.base_component import BaseComponent
from input_handlers import ActionOrHandler, AreaRangedAttackHandler, SingleRangedAttackHandler
import actions
import color
import components.ai

if TYPE_CHECKING:
    from entity import Actor


class Skill:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.parent: Optional[SkillTree] = None

    @property
    def engine(self):
        return self.parent.parent.gamemap.engine

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this skill."""
        return actions.ItemAction(consumer, None) # Skills behave like items acting on the world

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this skill."""
        raise NotImplementedError()


class SkillTree(BaseComponent):
    parent: Actor

    def __init__(self, skills: List[Skill] = None):
        self.skills = skills or []
        for skill in self.skills:
            skill.parent = self

    def add_skill(self, skill: Skill):
        if not self.has_skill(skill.name):
            self.skills.append(skill)
            skill.parent = self
            self.engine.message_log.add_message(f"You learned a new skill: {skill.name}!", color.welcome_text)

    def has_skill(self, skill_name: str) -> bool:
        return any(skill.name == skill_name for skill in self.skills)

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None


class FireballSkill(Skill):
    def __init__(self, damage: int, radius: int):
        super().__init__(name="Fireball", description=f"Explosion doing {damage} damage in {radius} radius.")
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        self.engine.message_log.add_message("Select a target location for Fireball.", color.needs_target)
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, None, xy, skill=self),
        )

    def activate(self, action: actions.ItemAction) -> None:
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            from exceptions import Impossible
            raise Impossible("You cannot target an area that you cannot see.")

        targets_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                )
                actor.fighter.take_damage(self.damage)
                targets_hit = True

        if not targets_hit:
            from exceptions import Impossible
            raise Impossible("There are no targets in the radius.")


class HealSkill(Skill):
    def __init__(self, amount: int):
        super().__init__(name="Lesser Heal", description=f"Heal yourself for {amount} HP.")
        self.amount = amount

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        return actions.ItemAction(consumer, None, skill=self)

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You cast {self.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
        else:
            from exceptions import Impossible
            raise Impossible("Your health is already full.")


class LightningSkill(Skill):
    def __init__(self, damage: int, maximum_range: int):
        super().__init__(name="Lightning Bolt", description=f"Strike closest enemy for {damage} damage.")
        self.damage = damage
        self.maximum_range = maximum_range

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        return actions.ItemAction(consumer, None, skill=self)

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity
        target = None
        closest_distance = self.maximum_range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.engine.game_map.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        if target:
            self.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} with a loud thunder, for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
        else:
            from exceptions import Impossible
            raise Impossible("No enemy is close enough to strike.")


class BeamSkill(Skill):
    def __init__(self, damage: int, range: int):
        super().__init__(name="Beam", description=f"Shoots a linear beam for {damage} damage, piercing enemies.")
        self.damage = damage
        self.range = range

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        self.engine.message_log.add_message("Select direction for Beam.", color.needs_target)
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.ItemAction(consumer, None, xy, skill=self),
        )

    def activate(self, action: actions.ItemAction) -> None:
        from projectiles import Projectile
        import math

        consumer = action.entity
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy[0], target_xy[1]]:
             from exceptions import Impossible
             raise Impossible("You cannot target an area that you cannot see.")

        dx = target_xy[0] - consumer.x
        dy = target_xy[1] - consumer.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 0:
            dx_norm = 1 if dx > 0 else (-1 if dx < 0 else 0)
            dy_norm = 1 if dy > 0 else (-1 if dy < 0 else 0)
        else:
            dx_norm, dy_norm = consumer.facing_direction

        projectile = Projectile(
            engine=self.engine,
            actor=consumer,
            symbol="|", # Beam-like symbol
            color=(0, 255, 255),
            range=self.range,
            damage=self.damage,
            dx=dx_norm,
            dy=dy_norm
        )
        self.engine.active_projectiles.append(projectile)
        self.engine.message_log.add_message(
            f"You fire a beam!",
            color.player_atk
        )


# Alias for backward compatibility with saves that have MagicMissileSkill
MagicMissileSkill = BeamSkill
