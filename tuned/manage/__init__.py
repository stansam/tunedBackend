from tuned.manage.commands import (
    create_superuser,
    create_users,
    create_content,
    create_prices,
    create_services,
    create_samples,
    create_testimonials,
    create_faqs,
    create_blogs,
    seed_db,
)

def register_cli_commands(app):
    app.cli.add_command(create_superuser)
    app.cli.add_command(create_users)
    app.cli.add_command(create_content)
    app.cli.add_command(create_prices)
    app.cli.add_command(create_services)
    app.cli.add_command(create_samples)
    app.cli.add_command(create_testimonials)
    app.cli.add_command(create_faqs)
    app.cli.add_command(create_blogs)
    app.cli.add_command(seed_db)