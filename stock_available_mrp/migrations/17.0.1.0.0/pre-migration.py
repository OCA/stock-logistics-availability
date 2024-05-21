def migrate(cr, version):
    cr.execute(
        """SELECT id FROM ir_config_parameter
        WHERE key = 'stock_available_mrp.stock_available_mrp_based_on'"""
    )
    record = cr.fetchone()
    if record:
        query = """INSERT INTO ir_model_data (
            name,
            model,
            module,
            res_id,
            noupdate)
            VALUES (
                'default_stock_available_mrp_based_on',
                'ir.config_parameter',
                'stock_available_mrp',
                '%s',
                True)"""
        cr.execute(query, (record[0]))
