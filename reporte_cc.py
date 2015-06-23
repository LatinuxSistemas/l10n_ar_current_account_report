# -*- coding: latin1 -*-

import base64
from osv import fields, osv, orm
from tools.translate import _
import time 
import netsvc

class reporte_cuenta_corriente(osv.osv_memory):
    
    _name = "report_cc"
    _description = "Crear Reporte de Cuenta Corriente"
    _columns = {
    		'data': fields.binary('Archivo', readonly=True),
                'name': fields.char('Nombre de Reporte',64, readonly=True),
                'partner_id':fields.many2one('res.partner','Empresa',required=True),
                'state':fields.selection([('choose','choose'),('fin','fin')],string="estado"),
                }
                
    ##########################
    ### Factura de Cliente ###
    ##########################
    
    def create_report_cc_cliente(self,cr,uid,ids,context={}):
	
	logger=netsvc.Logger()                
        this = self.browse(cr, uid, ids)[0]
        facturas = self.pool.get('account.invoice')
        clientes = self.pool.get('res.partner')        
        facids = facturas.search(cr,uid,[('partner_id', '=',this.partner_id.id),('type','in',('out_invoice','out_refund','out_debit'))], context=None)
        fec_reporte = time.strftime("%d de %B de %Y")
        outp = this.partner_id.name+'\n'+'Reporte Cuenta Corriente '+';'+ fec_reporte +'\n'*2+'Fecha de Factura;Nro de Factura;Descripcion;Doc. Fuente;Base Imponible($);Total($);Estado'
        output=outp.encode('latin1')
                
        for idfac in facids:
                       
            factura_actual = facturas.read(cr,uid,idfac,['number','date_invoice','amount_total','pos_ar_id','denomination_id','name','date_due','origin','amount_untaxed','state'])             

	    # fecha factura
	    fec_factura =''
	    if factura_actual['date_invoice']:
	        fec_factura = time.strftime("%d/%m/%Y", time.strptime(factura_actual['date_invoice'], '%Y-%m-%d'))
#	    else:
#		fecha_creacion = facturas.perm_read(cr,uid,idfac,details=False)['create_date']
#	        fec_factura = time.strftime("%d/%m/%Y", time.strptime(fecha_creacion, '%Y-%m-%d'))
            
            # posicion fiscal            
            if factura_actual['pos_ar_id']:
            	pos_fisc=factura_actual['pos_ar_id'][1]
            elif factura_actual['denomination_id']:            	
            	pos_fisc=factura_actual['denomination_id'][1]
            else: 
            	pos_fisc=''
           
            #estado                        
            if factura_actual['state'] == 'draft':
            	estado='Borrador'
            elif factura_actual['state'] == 'paid':
            	estado='Pagada'
            elif factura_actual['state'] == 'open':
            	estado='Abierta'
            elif factura_actual['state'] in ('proforma','proforma2'):
            	estado='Proforma'
            elif factura_actual['state'] == 'cancel':
            	estado='Cancelada'
            else: 
            	estado=''
            	
	    ##### HOJA DE REPORTE #####	            
            
            out = '\n' + (fec_factura or '') + ';' + pos_fisc + ' - ' + (factura_actual['number'] or '') + ';' + (factura_actual['name'] or 'sin descripcion').replace('\n',' ') + ';' + (factura_actual['origin'] or 'no esp.') + ';' + ('%.2f' % factura_actual['amount_untaxed']).replace('.',',') + ';' + ('%.2f' % factura_actual['amount_total']).replace('.',',') + ';' + estado
            try:
                if isinstance(out,unicode):
                    output+=out.encode('latin1')
                else:
                    output+=out
            except UnicodeEncodeError,data:                
                logger.notifyChannel("warning", netsvc.LOG_WARNING,'Problemas con caracteres ascii en la factura (id: %i), esta linea del reporte se pasa por alto!\n%s' % (idfac,data))
                     
        try:    
            salida=base64.encodestring(output)           
	except UnicodeEncodeError,data:
	    logger.notifyChannel("warning", netsvc.LOG_WARNING,"Error en el reporte, se deja sin completar!\n%s" % data)
	    salida=''
        return self.write(cr, uid, ids, {'state':'fin', 'data':salida, 'name':'reporte_cuenta_corriente.csv'}, context=context)
		
    ############################    
    ### Factura de Proveedor ###
    ############################

    def create_report_cc_proveedor(self,cr,uid,ids,context={}):
	
	logger=netsvc.Logger()        
        this = self.browse(cr, uid, ids)[0]
        facturas = self.pool.get('account.invoice')
        clientes = self.pool.get('res.partner')        
        facids = facturas.search(cr,uid,[('partner_id', '=',this.partner_id.id),('type','in',('in_invoice','in_refund','in_debit'))], context=None)
        fec_reporte = time.strftime("%d de %B de %Y")
        outp = this.partner_id.name+'\n'+'Reporte Cuenta Corriente '+';'+ fec_reporte +'\n'*2+'Fecha de Factura;Nro de Factura;Descripcion;Fec. Vencimiento;Doc. Fuente;Base Imponible($);Total($);Estado'
        output=outp.encode('latin1')
                
        for idfac in facids:
                       
            factura_actual = facturas.read(cr,uid,idfac,['number','date_invoice','amount_total','pos_ar_id','denomination_id','reference','date_due','origin','amount_untaxed','state'])             
            fec_factura=''
            if factura_actual['date_invoice']:
            	fec_factura = time.strftime("%d/%m/%Y", time.strptime(factura_actual['date_invoice'], '%Y-%m-%d'))
            
            # posicion fiscal            
            if factura_actual['pos_ar_id']:
            	pos_fisc=factura_actual['pos_ar_id'][1]
            elif factura_actual['denomination_id']:            	
            	pos_fisc=factura_actual['denomination_id'][1]
            else:
            	pos_fisc=''
            
            #estado            
            if factura_actual['state'] == 'draft':
            	estado='Borrador'
            elif factura_actual['state'] == 'paid':
            	estado='Pagada'
            elif factura_actual['state'] == 'open':
            	estado='Abierta'
            elif factura_actual['state'] in ('proforma','proforma2'):
            	estado='Proforma'
            elif factura_actual['state'] == 'cancel':
            	estado='Cancelada'
            else:            
	        estado=''
            	            	
	    ##### HOJA DE REPORTE #####	            
         
            out = '\n' + (fec_factura or '') + ';' + pos_fisc + ' - ' + (factura_actual['number'] or '') + ';' + (factura_actual['reference'] or 'sin descripcion').replace('\n',' ') + ';'+ (factura_actual['date_due'] or 'no especificada') + ';' + (factura_actual['origin'] or 'no esp.') + ';' + ('%.2f' % factura_actual['amount_untaxed']).replace('.',',') + ';' + ('%.2f' % factura_actual['amount_total']).replace('.',',') + ';' + estado
            try:
                if isinstance(out,unicode):
                    output+=out.encode('latin1')
                else:
                    output+=out
            except UnicodeEncodeError,data:                
                logger.notifyChannel("warning", netsvc.LOG_WARNING,'Problemas con caracteres ascii en la factura (id: %i), esta linea del reporte se pasa por alto!\n%s' % (idfac,data))
                #output+='\n'
            
        try:    
            salida=base64.encodestring(output)           
	except UnicodeEncodeError,data:	    
	    logger.notifyChannel("warning", netsvc.LOG_WARNING,"Error en el reporte, se deja sin completar!\n%s" % data)
	    salida=''
	    
        return self.write(cr, uid, ids, {'state':'fin', 'data':salida, 'name':'reporte_cuenta_corriente.csv'}, context=context)
	                   
    _defaults = {
                 'state': lambda *a: 'choose',          
                }
       
reporte_cuenta_corriente()
