'use strict';
// The browser edits explicit graph commands; Python owns all device geometry.
const $ = id => document.getElementById(id);
const token = JSON.parse($('bootstrap').textContent).token;
const svg = $('canvas');
let state, mode = 'draw', selected = null, hover = null, view = null;
let polygon = [], gesture = null, space = false, pending = 0, chain = Promise.resolve();
let crossingResolve = null, toastTimer;
const names = {draw:'绘制域壁',select:'选择对象',move:'移动节点',A:'指定 A 相',B:'指定 B 相',boundary:'手绘外边界'};
const colors = {A:'#b96879', B:'#387f86', none:'#9aa6b2'};
const fills = {A:'#f6e5e9', B:'#e0f1f1', none:'#f0f3f6'};

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 5000);
}
async function api(route, data) {
  const response = await fetch(route, {method:data === undefined ? 'GET':'POST',
    headers:{'Content-Type':'application/json','X-TPC-Session':token},
    ...(data === undefined ? {} : {body:JSON.stringify(data)})});
  const body = await response.json();
  if (!response.ok) {const error = new Error(body.error || '请求失败'); error.data = body; throw error;}
  return body;
}
function accept(value) {state=value; if (selected && !state.scene.nodes[selected] && !state.scene.edges[selected]) selected=null; render();}
function chooseCrossing(data) {
  $('crossing-info').textContent = `发现 ${data.crossings.length} 个交点。只有域壁合法格点才允许建立连接。`;
  $('cross-connect').disabled = data.crossings.some(p => !p.connectable);
  $('crossing-dialog').showModal();
  return new Promise(resolve => crossingResolve=resolve);
}
function run(command) {
  pending++; $('loading').hidden=false;
  const task = chain.then(async () => {
    try {accept(await api('/api/command',command)); return true;}
    catch(error) {
      if(error.data?.crossings) {
        const decision=await chooseCrossing(error.data);
        if(decision) {accept(await api('/api/command',{...command,crossing:decision})); return true;}
      } else toast(error.message);
      return false;
    }
  }).catch(error => {toast(error.message); return false;}).finally(() => {pending--; $('loading').hidden=pending===0;});
  chain=task; return task;
}
function setMode(value) {
  mode=value; polygon=[]; hover=null;
  document.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('active',b.dataset.mode===mode));
  svg.setAttribute('class','mode-'+mode); renderHints(); renderGhost();
}
function renderHints() {
  if(!state) return;
  $('mode-title').textContent=names[mode];
  const active=state.document.strokes.find(s=>s.id===state.document.active_stroke);
  const hint = {
    draw:!state.document.parameters.confirmed?'先核对左侧晶胞参数，再点击确认。':active?'点击下一拐点或终点；结束本段后可另画分支。':'点击域壁可选点开始；点击已有节点可接出新分支。',
    select:'点击节点或线段查看尺寸；右侧可输入精确坐标。',
    move:'拖动已有节点到另一个域壁格点；非法方向会回退。',
    A:'点击一个区域，将它指定为 A 相。',B:'点击一个区域，将它指定为 B 相。',
    boundary:`依次点击边界顶点（已选 ${polygon.length} 个）；Enter 闭合，Esc 取消。`
  };
  $('mode-hint').textContent=hint[mode];
  $('active-path').textContent=active?`${active.id} · 从 ${active.nodes.at(-1)} 继续`:'未在续画 · 可开始新路径';
}
function fit() {
  if(!state) return;
  const [xmin,ymin,xmax,ymax]=state.scene.bounds;
  const pad=Math.max(xmax-xmin,ymax-ymin)*.13;
  view=[xmin-pad,-ymax-pad,xmax-xmin+2*pad,ymax-ymin+2*pad];
  updateView();
}
function updateView(){if(view) svg.setAttribute('viewBox',view.join(' '));}
function world(event) {
  const point=new DOMPoint(event.clientX,event.clientY).matrixTransform(svg.getScreenCTM().inverse());
  return [point.x,-point.y];
}
function pixelDistance(xy,event) {
  const pt=new DOMPoint(xy[0],-xy[1]).matrixTransform(svg.getScreenCTM());
  return Math.hypot(pt.x-event.clientX,pt.y-event.clientY);
}
function nearest(event) {
  let best=null,dist=18;
  for(const p of state.scene.snap_points) {const d=pixelDistance(p.xy,event); if(d<dist){best=p;dist=d;}}
  return best;
}
function nodeAt(event) {
  let best=null,dist=15;
  for(const [id,n] of Object.entries(state.scene.nodes)){const d=pixelDistance(n.xy,event); if(d<dist){best=id;dist=d;}}
  return best;
}
function path(rings) {
  return rings.map(ring=>'M'+ring.map(pt=>pt[0]+','+(-pt[1])).join(' L')+' Z').join(' ');
}
function linePoints(points){return points.map(p=>p[0]+','+(-p[1])).join(' ');}
function renderGeometry() {
  const s=state.scene,p=state.document.parameters,a=p.a;
  const parts=[];
  for(const f of s.faces) parts.push(`<path class="geom-face" data-face="${f.id}" d="${path(f.rings)}" fill="${fills[f.phase||'none']}" fill-rule="evenodd" stroke="none"/>`);
  if($('show-holes').checked) for(const h of s.holes) parts.push(`<path d="${path([h.vertices])}" fill="${h.conflict?'#cb5042':colors[h.phase||'none']}" opacity="${h.phase ? 0.85 : 0.28}" pointer-events="none"/>`);
  if($('show-omitted').checked) for(const h of s.omitted_holes) parts.push(`<path d="${path([h.vertices])}" fill="none" stroke="#b3a69a" stroke-width="${a*.004}" stroke-dasharray="${a*.04} ${a*.025}" pointer-events="none"/>`);
  parts.push(`<path d="${path([state.document.boundary])}" fill="none" stroke="#8396a7" stroke-width="${a*.008}" pointer-events="none"/>`);
  if($('show-points').checked) {
    const lookup=new Map(s.snap_points.map(pt=>[pt.r+','+pt.c,pt]));
    for(const pt of s.snap_points) {
      for(const [dr,dc] of [[0,1],[1,0],[1,-1]]) {
        const end=lookup.get((pt.r+dr)+','+(pt.c+dc));
        if(end)parts.push(`<polyline points="${linePoints([pt.xy,end.xy])}" fill="none" stroke="#bdccd9" stroke-width="${a*.004}" opacity=".55" pointer-events="none"/>`);
      }
      parts.push(`<circle cx="${pt.xy[0]}" cy="${-pt.xy[1]}" r="${a*.023}" fill="#58748e" opacity=".8" pointer-events="none"/>`);
    }
  }
  for(const [id,e] of Object.entries(s.edges)) {
    const active=selected===id;
    parts.push(`<polyline points="${linePoints(e.xy)}" fill="none" stroke="${active?'#da8c33':'#254f76'}" stroke-width="${a*(active?.035:.02)}" stroke-linecap="round" pointer-events="none"/>`);
    if(mode==='select') parts.push(`<polyline class="geom-edge" data-edge="${id}" points="${linePoints(e.xy)}" fill="none" stroke="transparent" stroke-width="${a*.12}"/>`);
  }
  for(const [id,n] of Object.entries(s.nodes)) {
    const active=selected===id;
    parts.push(`<circle class="geom-node" data-node="${id}" cx="${n.xy[0]}" cy="${-n.xy[1]}" r="${a*(active?.065:.04)}" fill="${active?'#d78b39':'#fafcfd'}" stroke="#254f76" stroke-width="${a*.012}"/>`);
    if($('show-labels').checked) parts.push(`<text x="${n.xy[0]+a*.08}" y="${-n.xy[1]-a*.07}" font-family="Consolas,monospace" font-size="${a*.14}" fill="#254f76" pointer-events="none">${id}</text>`);
  }
  for(const cross of s.crossings) parts.push(`<circle cx="${cross.xy[0]}" cy="${-cross.xy[1]}" r="${a*.12}" fill="none" stroke="#c24e3f" stroke-width="${a*.015}" stroke-dasharray="${a*.04} ${a*.025}" pointer-events="none"/>`);
  $('scene').innerHTML=parts.join(''); renderGhost();
}
function renderGhost() {
  if(!state) return;
  const a=state.document.parameters.a,parts=[];
  if(mode==='boundary' && polygon.length) {
    const points=hover?[...polygon,hover.xy]:polygon;
    parts.push(`<polyline points="${linePoints(points)}" fill="none" stroke="#bd7e36" stroke-width="${a*.02}" stroke-dasharray="${a*.08} ${a*.04}"/>`);
    for(const p of polygon) parts.push(`<circle cx="${p[0]}" cy="${-p[1]}" r="${a*.04}" fill="#bd7e36"/>`);
  } else if(hover) {
    const active=state.document.strokes.find(s=>s.id===state.document.active_stroke);
    if(active && mode==='draw') {
      const last=state.scene.nodes[active.nodes.at(-1)];
      const dr=hover.r-last.r,dc=hover.c-last.c;
      const valid=dr===0||dc===0||dr===-dc;
      parts.push(`<polyline points="${linePoints([last.xy,hover.xy])}" stroke="${valid?'#3978a8':'#c75c4d'}" stroke-width="${a*.015}" stroke-dasharray="${a*.06} ${a*.04}" fill="none"/>`);
    }
    parts.push(`<circle cx="${hover.xy[0]}" cy="${-hover.xy[1]}" r="${a*.065}" fill="none" stroke="#3978a8" stroke-width="${a*.012}"/>`);
  }
  $('ghost').innerHTML=parts.join(''); $('ghost').setAttribute('pointer-events','none');
}
function renderSelection() {
  const n=state.scene.nodes[selected],e=state.scene.edges[selected];
  $('node-properties').hidden=!n; $('delete').disabled=!n&&!e;
  if(n) {
    $('selection').innerHTML=`<strong>${selected}</strong><p class="measure">r=${n.r}　c=${n.c}</p><p class="measure">x=${n.xy[0].toPrecision(6)} mm<br>y=${n.xy[1].toPrecision(6)} mm</p>`;
    $('node-r').value=n.r; $('node-c').value=n.c;
  } else if(e) {
    const strokes=state.document.strokes.filter(s=>s.nodes.some((n,i)=>i&&new Set([n,s.nodes[i-1]]).has(e.u)&&new Set([n,s.nodes[i-1]]).has(e.v)));
    $('selection').innerHTML=`<strong>${selected}</strong><p>${e.u} — ${e.v}</p><p class="measure">长度 ${e.length.toPrecision(6)} mm<br>${e.periods} 个晶格间隔</p><p>涉及路径：${strokes.map(s=>s.id).join('、')||'—'}</p>`;
  } else $('selection').textContent='选择节点或线段，查看坐标与尺寸。';
}
function render() {
  const doc=state.document,s=state.scene,p=doc.parameters;
  if(!$('parameters').contains(document.activeElement)) {
    for(const [id,value] of Object.entries({a:p.a,large:p.large_ratio,small:p.small_ratio,topology:p.topology,ox:p.origin[0],oy:p.origin[1]})) $(id).value=value;
  }
  if(!$('rectangle').contains(document.activeElement)) {
    const [xmin,ymin,xmax,ymax]=s.bounds;
    for(const [id,value] of Object.entries({xmin,ymin,xmax,ymax})) $(id).value=Number(value.toPrecision(10));
  }
  $('boundary-kind').textContent=doc.boundary.length===4?'四边形':'自定义';
  $('preset-state').textContent=p.confirmed?'已确认 · 可开始绘制域壁':'示例参数 · 请先核对';
  $('confirm-preset').textContent=p.confirmed?'已确认晶胞与域壁点':'已核对，确认晶胞与域壁点';
  $('confirm-preset').disabled=p.confirmed;
  $('undo').disabled=!state.undo; $('redo').disabled=!state.redo;
  $('dirty').textContent=(state.dirty?'● ':'')+state.filename;
  document.title=(state.dirty?'* ':'')+'TPC · 域壁路径编辑器';
  $('stats').textContent=`${Object.keys(doc.nodes).length} 点 / ${Object.keys(doc.edges).length} 段 / ${doc.strokes.length} 条路径`;
  $('scale-label').textContent=`宽 ${(s.bounds[2]-s.bounds[0]).toPrecision(5)} mm · 高 ${(s.bounds[3]-s.bounds[1]).toPrecision(5)} mm · a=${p.a} mm`;
  const list=$('checks'); list.replaceChildren();
  $('check-count').textContent=s.checks.length?'待处理 '+s.checks.length:'通过';
  for(const c of s.checks) {
    const b=document.createElement('button');b.className='check-item '+c.level;b.textContent=c.message;
    b.onclick=()=>{selected=c.target; if(c.xy)focusAt(c.xy); else if(s.nodes[selected])focusAt(s.nodes[selected].xy); else if(s.edges[selected])focusAt(s.edges[selected].xy[0]); renderSelection();renderGeometry();};
    list.append(b);
  }
  if(!s.checks.length){const el=document.createElement('div');el.className='check-item good';el.textContent='当前几何检查通过。';list.append(el);}
  const nodes=$('node-list');nodes.replaceChildren();
  $('node-count').textContent=Object.keys(doc.nodes).length;
  for(const [id,n] of Object.entries(s.nodes)){
    const b=document.createElement('button');b.className='node-row'+(selected===id?' selected':'');
    const label=document.createElement('span');label.textContent=id;
    const pos=document.createElement('span');pos.textContent=`(${n.r}, ${n.c})`;
    b.append(label,pos);b.onclick=()=>{selected=id;setMode('select');render();};nodes.append(b);
  }
  if(!nodes.children.length)nodes.textContent='尚未选择路径点';
  $('fill-summary').textContent=`${s.faces.filter(f=>f.phase).length}/${s.faces.length} 个区域已分相；${s.holes.length} 个完整孔，外边缘未放置 ${s.omitted_holes.length} 个孔。`;
  renderHints();renderSelection();renderGeometry();if(!view)fit();
}
function focusAt(pt){if(view){view[0]=pt[0]-view[2]/2;view[1]=-pt[1]-view[3]/2;updateView();}}
function zoom(factor,position){if(!view)return;const cx=position?.[0]??view[0]+view[2]/2,cy=position?.[1]??view[1]+view[3]/2;view=[cx+(view[0]-cx)*factor,cy+(view[1]-cy)*factor,view[2]*factor,view[3]*factor];updateView();}
svg.addEventListener('wheel',event=>{event.preventDefault();const p=world(event);zoom(event.deltaY>0?1.12:1/1.12,[p[0],-p[1]]);},{passive:false});
svg.addEventListener('pointerdown',event=>{
  if(!state||pending||event.button===2)return;
  const xy=world(event),node=nodeAt(event);
  if(event.button===1||space){gesture={type:'pan',screen:[event.clientX,event.clientY],view:[...view]};event.preventDefault();}
  else if(mode==='move'&&node){gesture={type:'move',node,start:[event.clientX,event.clientY]};selected=node;renderSelection();}
  else gesture={type:'click',start:[event.clientX,event.clientY]};
  svg.setPointerCapture(event.pointerId);
});
svg.addEventListener('pointermove',event=>{
  if(!state)return;
  const xy=world(event);
  if(gesture?.type==='pan'){
    const rect=svg.getBoundingClientRect();const scale=Math.min(rect.width/gesture.view[2],rect.height/gesture.view[3]);
    view=[gesture.view[0]-(event.clientX-gesture.screen[0])/scale,gesture.view[1]-(event.clientY-gesture.screen[1])/scale,gesture.view[2],gesture.view[3]];updateView();return;
  }
  hover=mode==='boundary'?{xy}:nearest(event);
  $('cursor').textContent=hover&&mode!=='boundary'?`r ${hover.r}　c ${hover.c}　x ${hover.xy[0].toFixed(5)}　y ${hover.xy[1].toFixed(5)} mm`:`x ${xy[0].toFixed(5)}　y ${xy[1].toFixed(5)} mm`;
  renderGhost();
});
svg.addEventListener('pointerup',async event=>{
  if(!state||!gesture)return;
  const action=gesture;gesture=null;
  if(action.type==='pan')return;
  const snapped=nearest(event);
  if(action.type==='move'){
    if(snapped)await run({type:'move',id:action.node,r:snapped.r,c:snapped.c});
    else toast('请将节点放到一个可选域壁点上');return;
  }
  if(Math.hypot(event.clientX-action.start[0],event.clientY-action.start[1])>7)return;
  if(mode==='boundary'){
    const xy=world(event);
    if(polygon.length>=3&&pixelDistance(polygon[0],event)<15)finishBoundary();
    else {polygon.push(xy);renderHints();renderGhost();}return;
  }
  if(mode==='draw'){
    if(!state.document.parameters.confirmed){toast('请先核对左侧晶胞预设并点击确认');return;}
    if(!snapped){toast('请点击一个域壁可选点，或放大画布后重试');return;}
    await run({type:'point',r:snapped.r,c:snapped.c,require_confirmed:true});return;
  }
  if(mode==='A'||mode==='B'){
    // Pointer capture retargets pointerup; use the element physically under the cursor.
    const face=document.elementFromPoint(event.clientX,event.clientY)?.closest('[data-face]');
    if(face)await run({type:'phase',region:face.dataset.face,phase:mode});
    else toast('请点击相区内部，避开节点和线段');return;
  }
  const element=document.elementFromPoint(event.clientX,event.clientY);
  selected=nodeAt(event)||element?.closest('[data-edge]')?.dataset.edge||null;render();
});
svg.addEventListener('pointercancel',()=>gesture=null);
svg.addEventListener('pointerleave',()=>{if(!gesture){hover=null;renderGhost();}});
async function finishBoundary(){if(polygon.length<3){toast('闭合边界至少需要三个顶点');return;}if(await run({type:'boundary',points:polygon})){setMode('select');fit();}}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{setMode(b.dataset.mode);renderGeometry();});
for(const id of ['show-points','show-holes','show-omitted','show-labels'])$(id).onchange=renderGeometry;
$('end').onclick=()=>mode==='boundary'?finishBoundary():run({type:'end'});
$('undo').onclick=()=>run({type:'undo'});$('redo').onclick=()=>run({type:'redo'});
$('fit').onclick=fit;$('zoom-in').onclick=()=>zoom(1/1.3);$('zoom-out').onclick=()=>zoom(1.3);
$('polygon').onclick=()=>{setMode('boundary');toast('点击外边界顶点，Enter 闭合，Esc 取消');};
$('parameters').onsubmit=async event=>{event.preventDefault();await run({type:'parameters',values:{a:+$('a').value,large_ratio:+$('large').value,small_ratio:+$('small').value,topology:$('topology').value,origin:[+$('ox').value,+$('oy').value]}});};
$('confirm-preset').onclick=()=>run({type:'parameters',values:{confirmed:true}});
$('rectangle').onsubmit=async event=>{event.preventDefault();const x0=+$('xmin').value,x1=+$('xmax').value,y0=+$('ymin').value,y1=+$('ymax').value;if(x1<=x0||y1<=y0){toast('最大坐标需要大于最小坐标');return;}if(await run({type:'boundary',points:[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]}))fit();};
$('node-properties').onsubmit=event=>{event.preventDefault();if(selected)run({type:'move',id:selected,r:+$('node-r').value,c:+$('node-c').value});};
$('delete').onclick=()=>{if(selected)run({type:'delete',id:selected});};
document.addEventListener('keydown',event=>{
  if(document.querySelector('dialog[open]'))return;
  if(['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName))return;
  if(event.code==='Space'){space=true;event.preventDefault();}
  if(event.key==='Escape'){if(mode==='boundary')setMode('draw');else run({type:'end'});}
  if(event.key==='Enter'&&mode==='boundary')finishBoundary();
  if(event.key==='Delete'&&selected){event.preventDefault();run({type:'delete',id:selected});}
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'){event.preventDefault();run({type:event.shiftKey?'redo':'undo'});}
});
document.addEventListener('keyup',event=>{if(event.code==='Space')space=false;});
for(const [id,value] of [['cross-cancel',null],['cross-separate','separate'],['cross-connect','connect']])$(id).onclick=()=>{$('crossing-dialog').close();crossingResolve?.(value);crossingResolve=null;};
$('crossing-dialog').addEventListener('cancel',()=>{crossingResolve?.(null);crossingResolve=null;});
async function download(format) {
  $('loading').hidden=false;
  try {const response=await fetch('/api/export?format='+format,{headers:{'X-TPC-Session':token}});if(!response.ok)throw new Error((await response.json()).error);const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=state.filename.replace(/\.json$/i,'')+'.'+format;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('已导出 '+format.toUpperCase());}
  catch(error){toast(error.message);}finally{$('loading').hidden=false;setTimeout(()=>$('loading').hidden=pending===0,100);}
}
$('save').onclick=()=>{$('save-workspace').textContent=state.workspace;$('save-name').value=state.filename;$('save-error').textContent='';$('save-dialog').showModal();};
$('save-cancel').onclick=()=>$('save-dialog').close();
$('save-download').onclick=()=>{download('json');$('save-dialog').close();};
$('save-submit').onclick=async()=>{
  const name=$('save-name').value;
  try{let result;try{result=await api('/api/save',{name});}catch(error){if(error.data?.exists&&confirm('文件已存在，是否覆盖 '+name+'？'))result=await api('/api/save',{name,overwrite:true});else throw error;}accept(result);$('save-dialog').close();toast('已保存到 '+result.saved_path);}
  catch(error){$('save-error').textContent=error.message;}
};
$('export').onclick=()=>{
  document.querySelector('[data-export="dxf"]').disabled=!state.scene.ready;
  $('export-state').textContent=state.scene.ready?'当前几何检查通过。':`当前有 ${state.scene.checks.length} 项待处理，可先导出草稿图，完成检查后可导出 DXF。`;
  $('export-dialog').showModal();
};
$('export-cancel').onclick=()=>$('export-dialog').close();
document.querySelectorAll('[data-export]').forEach(b=>b.onclick=()=>{download(b.dataset.export);$('export-dialog').close();});
$('new').onclick=async()=>{if(!state.dirty||confirm('当前修改尚未保存，是否新建设计？')){await run({type:'new'});selected=null;setMode('draw');fit();}};
$('open').onclick=()=>$('file-input').click();
$('file-input').onchange=async event=>{const file=event.target.files[0];if(!file)return;try{if(state.dirty&&!confirm('当前修改尚未保存，是否打开另一个设计？'))return;const value=JSON.parse(await file.text());accept(await api('/api/replace',{document:value}));selected=null;setMode('select');fit();toast('已打开 '+file.name);}catch(error){toast(error.message);}finally{event.target.value='';}};
$('stop').onclick=async()=>{if(confirm(state.dirty?'当前有未保存修改。确定停止编辑服务？':'确定停止本机编辑服务？')){await api('/api/stop',{});toast('服务已停止，已保存的设计文件仍在工作目录');state.dirty=false;}};
window.addEventListener('beforeunload',event=>{if(state?.dirty){event.preventDefault();event.returnValue='';}});
api('/api/state').then(value=>{accept(value);setMode('draw');}).catch(error=>toast('无法连接本机编辑服务：'+error.message));
