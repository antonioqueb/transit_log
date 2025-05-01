# -*- coding: utf-8 -*-
{
    "name": "Bitácora de Tránsitos A-B",
    "version": "1.0",
    "summary": "Registro de movimientos de transporte sin impacto en inventario",
    "author": "Alphaqueb Consulting",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["mail", "product", "uom"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/transit_log_views.xml",
    ],
    "application": False,
    "installable": True,
}
