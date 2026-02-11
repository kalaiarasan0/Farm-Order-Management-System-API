"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_default():
    ${default_upgrades if default_upgrades else "pass"}


def upgrade_user():
    ${user_upgrades if user_upgrades else "pass"}

def downgrade_default():
    ${default_downgrades if default_downgrades else "pass"}


def downgrade_user():
    ${user_downgrades if user_downgrades else "pass"}