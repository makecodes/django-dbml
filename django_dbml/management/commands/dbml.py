import logging

from django.core.management.base import BaseCommand

from django_dbml.core import GenerationOptions, generate_dbml

logger = logging.getLogger("dbml")


class Command(BaseCommand):
    help = "Generate a DBML file based on Django models"

    def add_arguments(self, parser):  # noqa: D102
        # fmt: off
        parser.add_argument("args", metavar="app_label[.ModelName]", nargs="*", help="Restricts dbml generation to the specified app_label or app_label.ModelName.")
        parser.add_argument("--table_names", action="store_true", help="Use underlying table names rather than model names")
        parser.add_argument("--group_by_app", action="store_true")
        parser.add_argument("--color_by_app", action="store_true")
        parser.add_argument("--add_project_name", action="store", help="add name for the project")
        parser.add_argument("--add_project_notes", action="store", help="add notes to describe the project")
        parser.add_argument("--disable_update_timestamp", action="store_true", help="do not include a 'Last updated at' timestamp in the project notes.")
        parser.add_argument("--output_file", action="store", help="Put the generated schema in this file, rather than printing it to stdout.")
        # fmt: on

    def handle(self, *app_labels, **kwargs):  # noqa: D102
        options = GenerationOptions.from_command_kwargs(kwargs)
        output = generate_dbml(app_labels, options)

        if options.output_file:
            options.output_file.write_text(output, encoding="utf-8")
            logger.info("Generated dbml file to %s", options.output_file)
            return

        self.stdout.write(output, ending="")
