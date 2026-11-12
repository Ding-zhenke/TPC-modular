"""Offline-first slotted fork waveguide with native CST geometry adapter."""
import json
from pathlib import Path
from mesh_grid.metal_hex.fork_waveguide import ForkWaveguideSpec, build_fork_waveguide


class ForkWaveguide:
    def __init__(self,spec=None):
        self.spec=ForkWaveguideSpec() if spec is None else spec
        if not isinstance(self.spec,ForkWaveguideSpec):
            raise TypeError('spec must be ForkWaveguideSpec')

    def geometry(self):
        return build_fork_waveguide(self.spec)

    def build(self,app,*,prefix='mh',component='metal_hex'):
        from topo_modeler.builders.fork_waveguide import build_fork_waveguide_cst
        return build_fork_waveguide_cst(app,self.spec,prefix=prefix,component=component)

    def preview(self,output_dir):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from mesh_grid.metal_hex.plotting import _paint
        g=self.geometry();out=Path(output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
        paths={ext:out/f'fork_waveguide.{ext}' for ext in ('png','svg','json')}
        with plt.rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none'}):
            fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
            try:
                for role,color in [('substrate','#eaf0f4'),('rings','#a8622b'),
                                   ('phase_a','#218b91'),('phase_b','#6459a5'),
                                   ('probe_left','#cd6246'),('probe_right','#cd6246')]:
                    _paint(ax,g[role],color)
                xl,yl,xr,yr=g['substrate'].bounds
                ax.add_patch(Rectangle((xl,yl),xr-xl,yr-yl,fill=False,ec='#23313e'))
                ax.axhline(0,color='#bb3b48',ls='--',lw=.8)
                ax.set(xlim=(xl-.1,xr+.1),ylim=(yl-.1,yr+.1),aspect='equal',
                       xlabel='x / mm',ylabel='y / mm',title='AB fork waveguide: shared gap and symmetric stubs')
                for ext in ('png','svg'):fig.savefig(paths[ext],dpi=180)
            finally:plt.close(fig)
        payload={'spec':self.spec.to_dict(),'y_bounds_mm':self.spec.y_bounds,
                 'row_spacing_mm':self.spec.row_spacing,'metal_area_mm2':g['metal'].area,
                 'evidence':'offline geometry; no CST readback or solve'}
        paths['json'].write_text(json.dumps(payload,indent=2),encoding='utf-8')
        return paths
