-e ### models/transit_log.py
```
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime

class TransitLog(models.Model):
    _name = "transit.log"
    _description = "Bitácora de Tránsitos Punto A–B"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Cabecera
    name = fields.Char(
        string="Folio",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nuevo"),
    )
    date_start = fields.Datetime(
        string="Salida",
        tracking=True,
        default=lambda self: fields.Datetime.now(),
    )
    date_end = fields.Datetime(string="Llegada", tracking=True)
    origin = fields.Char(string="Origen", tracking=True, required=True)
    destination = fields.Char(string="Destino", tracking=True, required=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_transit", "En tránsito"),
            ("delivered", "Entregado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )

    line_ids = fields.One2many(
        "transit.log.line", "log_id", string="Productos transportados"
    )
    notes = fields.Text(string="Notas adicionales")

    # Secuencia automática
    @api.model
    def create(self, vals):
        if vals.get("name", _("Nuevo")) == _("Nuevo"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "transit.log.sequence"
            ) or _("Nuevo")
        return super().create(vals)

    # Acciones simples de flujo
    def action_start(self):
        self.state = "in_transit"

    def action_arrive(self):
        self.state = "delivered"
        self.date_end = fields.Datetime.now()

    def action_cancel(self):
        self.state = "cancelled"


class TransitLogLine(models.Model):
    _name = "transit.log.line"
    _description = "Detalle de productos en tránsito"

    log_id = fields.Many2one("transit.log", string="Bitácora", ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Producto", required=True
    )
    product_uom_qty = fields.Float(
        string="Cantidad", required=True, digits="Product Unit of Measure"
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="UdM",
        required=True,
        domain="[('category_id', '=', product_id.uom_id.category_id)]",
    )

    # Al seleccionar producto, proponemos la UdM por defecto
    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
```

-e ### models/__init__.py
```
# -*- coding: utf-8 -*-
from . import transit_log
```

-e ### views/transit_log_views.xml
```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Menú raíz -->
    <menuitem id="menu_transit_root"
              name="Tránsitos"
              sequence="10"/>

    <!-- Acción (debe ir antes de usarla en el menú) -->
    <record id="action_transit_log" model="ir.actions.act_window">
        <field name="name">Bitácora de Tránsitos</field>
        <field name="res_model">transit.log</field>
        <field name="view_mode">list,form</field>
        <field name="help" type="html">
            <p>
                Registra aquí cada movimiento directo a destino sin
                afectar inventario.
            </p>
        </field>
    </record>

    <!-- Menú que llama la acción -->
    <menuitem id="menu_transit_log"
              name="Bitácora"
              parent="menu_transit_root"
              action="action_transit_log"
              sequence="20"/>

    <!-- Vista lista -->
    <record id="view_transit_log_list" model="ir.ui.view">
        <field name="name">transit.log.list</field>
        <field name="model">transit.log</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="date_start"/>
                <field name="origin"/>
                <field name="destination"/>
                <field name="state"/>
            </list>
        </field>
    </record>

    <!-- Vista formulario -->
    <record id="view_transit_log_form" model="ir.ui.view">
        <field name="name">transit.log.form</field>
        <field name="model">transit.log</field>
        <field name="arch" type="xml">
            <form string="Bitácora de Tránsito" create="true" edit="true">
                <header>
                    <button name="action_start" type="object"
                            string="Salir" states="draft"
                            class="btn-primary"/>
                    <button name="action_arrive" type="object"
                            string="Llegada" states="in_transit"
                            class="btn-success"/>
                    <button name="action_cancel" type="object"
                            string="Cancelar" states="draft,in_transit"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,in_transit,delivered,cancelled"/>
                </header>

                <sheet>
                    <group>
                        <field name="name" readonly="1"/>
                        <field name="origin"/>
                        <field name="destination"/>
                        <field name="date_start"/>
                        <field name="date_end" attrs="{'invisible': [('state','!=','delivered')]}"/>
                    </group>

                    <notebook>
                        <page string="Productos">
                            <field name="line_ids" mode="tree,form">
                                <list>
                                    <field name="product_id"/>
                                    <field name="product_uom_qty"/>
                                    <field name="product_uom"/>
                                </list>
                                <form>
                                    <group>
                                        <field name="product_id"/>
                                        <field name="product_uom_qty"/>
                                        <field name="product_uom"/>
                                    </group>
                                </form>
                            </field>
                        </page>

                        <page string="Notas">
                            <field name="notes" placeholder="Observaciones relevantes…"/>
                        </page>
                    </notebook>
                </sheet>

                <div class="oe_chatter">
                    <field name="message_follower_ids" widget="mail_followers"/>
                    <field name="activity_ids" widget="mail_activity"/>
                    <field name="message_ids" widget="mail_thread"/>
                </div>
            </form>
        </field>
    </record>
</odoo>
```

### __init__.py
```
# -*- coding: utf-8 -*-
from . import models
```
### __manifest__.py
```
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
```
