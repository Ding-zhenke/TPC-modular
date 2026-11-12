"""Parametric CST command adapter for the slotted AB fork waveguide."""
from .metal_hex import build_metal_hex
from mesh_grid.metal_hex.fork_waveguide import ForkWaveguideSpec, build_fork_waveguide


def build_fork_waveguide_cst(app, spec=None, *, prefix='mh', component='metal_hex'):
    """Write only geometry to caller's clean mm project; no solver or ports."""
    spec=ForkWaveguideSpec() if spec is None else spec
    if not isinstance(spec,ForkWaveguideSpec):
        raise TypeError('spec must be ForkWaveguideSpec')
    build_fork_waveguide(spec)  # validate contact and support before any writes

    class ClippedApp:
        def __getattr__(self,name):
            return getattr(app,name)

        def para(self,name,value,**kwargs):
            result=app.para(name,value,**kwargs)
            if name=='dy':
                for key,val in [('ur',spec.upper_rows),('dr',spec.lower_rows),
                                ('yu','ur*dy/2'),('yd','dr*dy/2')]:
                    app.para(key,val)
            return result

        def polyline(self,data,**kwargs):
            mapping={'ym':'yu','-ym':'-yd'}
            return app.polyline([[x,mapping.get(y,y)] for x,y in data],**kwargs)

        def square(self,xmin,xmax,ymin,ymax,zmin,zmax,name,**kwargs):
            # Temporary base substrate is replaced after the feed is constructed.
            return app.square(xmin,xmax,'-yd','yu',zmin,zmax,name,**kwargs)

    base=build_metal_hex(ClippedApp(),spec.base_spec(),prefix=prefix,component=component)
    p=spec.probe
    params=[('g',p.gap),('w0',p.wide_width),('w1',p.arm_width),('l0',p.neck_length),
            ('lt',p.taper_length),('lv',p.fork_length),('lf',p.arm_length),
            ('ls',p.stub_length),('ws',p.stub_width),('ds',p.stub_distance),
            ('li',p.insertion),('mg2',spec.substrate_margin),('rh','d1*cosd(30)'),
            ('ed','-nx*a/2'),('tp','ed+li'),('ea','tp-lf'),('eb','ea-lt'),
            ('ec','eb-l0'),('fk','ea-lv'),('ov','g/2+w1'),('sc','tp-ds'),
            ('bx2','-ec+mg2')]
    for key,value in params: app.para(key,value)
    copper='Copper (annealed)'; curve=f'{prefix}_curves'
    def sheet(name,points):
        app.polyline(points+[points[0]],name=name,curve=curve)
        app.extrude(f'{curve}:{name}',name,'t',component=component,material=copper)
    def signed(expr,side):
        return expr if side=='left' else f'-({expr})'
    rings=base['shapes']['rings']
    for side in ('left','right'):
        sx=lambda x:signed(x,side)
        a,b=sx('ed-rh'),sx('ed+rh+li')
        slot=f'{prefix}_slot_{side}'
        sheet(slot,[[a,'-g/2'],[b,'-g/2'],[b,'g/2'],[a,'g/2']])
        app.subtract(rings,slot,component1=component,component2=component)
        points=[['ec','-w0/2'],['eb','-w0/2'],['ea','-ov'],['tp','-ov'],
                ['tp','-g/2'],['ea','-g/2'],['fk','0'],['ea','g/2'],
                ['tp','g/2'],['tp','ov'],['ea','ov'],['eb','w0/2'],['ec','w0/2']]
        name=f'{prefix}_probe_{side}'
        sheet(name,[[sx(x),y] for x,y in points])
        for label,y0,y1 in [('up','ov-0.005','ov+ls'),('dn','-ov-ls','-ov+0.005')]:
            stub=f'{prefix}_stub_{side}_{label}'
            sheet(stub,[[sx('sc-ws/2'),y0],[sx('sc+ws/2'),y0],
                        [sx('sc+ws/2'),y1],[sx('sc-ws/2'),y1]])
            app.add(name,stub,component1=component,component2=component)
        base['shapes'][f'probe_{side}']=name
    # The caller supplies a clean project. Delete the base substrate by the
    # public API, then create a wider substrate covering the two feeds.
    app.delete_solid(base['shapes']['substrate'],component=component)
    app.square('-bx2','bx2','-yd','yu','-h','0',base['shapes']['substrate'],
               component=component,material='Quartz (Fused) (lossy)')
    base['parameters'].update(dict(params))
    base['parameters'].update(ur=spec.upper_rows,dr=spec.lower_rows,yu='ur*dy/2',yd='dr*dy/2')
    return base
