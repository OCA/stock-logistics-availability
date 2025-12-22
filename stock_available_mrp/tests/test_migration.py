import os

from odoo.modules.migration import load_script
from odoo.tests.common import TransactionCase


class TestMigrations(TransactionCase):
    def get_migration_module(self, module, version, script="post-migration.py"):
        """Get the migration module.

        :param module: the addon that hosts the migration script.
        :param version: the <module>/migrations/<VERSION> subdirectory containing
        the migration script.
        :param script: the filename of the migration script.
        """
        pyfile = os.path.join(module, "migrations", version, script)
        name, ext = os.path.splitext(os.path.basename(pyfile))
        return load_script(pyfile, name)

    def run_migration(self, module, version, script="post-migration.py"):
        """Run a migration script.

        :param module: the addon that hosts the migration script.
        :param version: the <module>/migrations/<VERSION> subdirectory containing
        the migration script.
        :param script: the filename of the migration script.
        """
        mod = self.get_migration_module(module, version, script=script)
        mod.migrate(self.env.cr, version)
        self.env.invalidate_all()

    def test_config_parameter(self):
        """In 17.0, the configuration option was actually unused."""
        new_key = "stock_available_mrp.stock_available_mrp_based_on"
        old_key = "stock_available_mrp_based_on"
        # Let's say that in 17.0, someone once configured 'virtual_available'
        # as the field to base mrp potential on.
        self.env["ir.config_parameter"].set_param(new_key, "virtual_available")
        # But in the code, a different parameter was used. For this parameter,
        # a default was set using xml data.
        self.env["ir.config_parameter"].set_param(old_key, "qty_available")
        # We don't want anything to change after the migration, so we copy
        # the field name that was actually used to determine the computation
        # to the configuration parameter that is going to be used in 18.0.
        self.run_migration("stock_available_mrp", "18.0.1.0.0", "post-migration.py")
        self.assertEqual(
            self.env["ir.config_parameter"].get_param(new_key), "qty_available"
        )
