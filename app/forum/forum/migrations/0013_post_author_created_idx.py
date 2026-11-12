from django.db import migrations, models


class Migration(migrations.Migration):
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    atomic = False

    dependencies = [
        ('forum', '0012_remove_unused_fields'),
    ]

    operations = [
        # IF NOT EXISTS: the index was first created by hand in production.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='CREATE INDEX CONCURRENTLY IF NOT EXISTS '
                        'forum_post_author_created_idx '
                        'ON forum_post (author_id, created DESC);',
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS '
                                'forum_post_author_created_idx;',
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='post',
                    index=models.Index(
                        fields=['author', '-created'],
                        name='forum_post_author_created_idx'),
                ),
            ],
        ),
    ]
