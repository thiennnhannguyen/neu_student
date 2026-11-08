import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name, disable_existing_loggers=False)
logger = logging.getLogger('alembic.env')


def get_engine():
    return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        # Batch alter của SQLite tạo lại bảng. Bảng đang có bảng con trỏ tới (vd quiz_questions)
        # thì DROP TABLE vi phạm khóa ngoại dù bảng mới mang lại đúng tên ngay sau đó. PRAGMA
        # foreign_keys chỉ đổi được ngoài transaction, nên gọi thẳng trên kết nối DBAPI trước
        # BEGIN; kiểm foreign_key_check trước khi commit và luôn bật lại khóa ngoại.
        raw = connection.connection.driver_connection
        sqlite = connection.dialect.name == 'sqlite'
        if sqlite:
            raw.execute('PRAGMA foreign_keys=OFF')
        finished = False
        try:
            with context.begin_transaction():
                context.run_migrations()
                if sqlite:
                    broken = connection.exec_driver_sql('PRAGMA foreign_key_check').all()
                    if broken:
                        raise RuntimeError(f'Migration làm hỏng khóa ngoại: {broken[:5]}')
            finished = True
        finally:
            if sqlite:
                # PRAGMA trong transaction đang mở không có tác dụng: đóng transaction trước.
                if connection.in_transaction():
                    if finished:
                        connection.commit()
                    else:
                        connection.rollback()
                raw.execute('PRAGMA foreign_keys=ON')
                if raw.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
                    raise RuntimeError('Không bật lại được khóa ngoại sau migration')


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
