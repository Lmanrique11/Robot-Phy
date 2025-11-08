// --- Utilities ---
function linspace(a,b,n){ const arr=[]; if(n===1) return [a]; const step=(b-a)/(n-1); for(let i=0;i<n;i++) arr.push(a+i*step); return arr }
function mean(arr){ return arr.reduce((s,v)=>s+v,0)/arr.length }
function median(arr){ const a=[...arr].sort((x,y)=>x-y); const m=Math.floor(a.length/2); return a.length%2?a[m]:(a[m-1]+a[m])/2 }
function std(arr){ const m=mean(arr); return Math.sqrt(arr.reduce((s,v)=>s+(v-m)*(v-m),0)/arr.length) }
function min(arr){ return Math.min(...arr) }
function max(arr){ return Math.max(...arr) }
function movingAverage(data, window){ if(window<=1) return data.slice(); const out=[]; const half=Math.floor(window/2); for(let i=0;i<data.length;i++){ let s=0,c=0; for(let j=Math.max(0,i-half); j<=Math.min(data.length-1,i+half); j++){ s+=data[j]; c++ } out.push(s/c) } return out }

// --- Generate datasets ---
function generate(name,n){
    if(name==='sine' || name==='sine-noisy'){
    const x=linspace(0,4*Math.PI,n);
    const y=x.map(t=>Math.sin(t));
    if(name==='sine-noisy'){
        for(let i=0;i<n;i++) y[i]+= (Math.random()-0.5)*0.4; }
    return {x,y}
    }
    if(name==='scatter'){
    const x=[],y=[]; for(let i=0;i<n;i++){ x.push(Math.random()*10); y.push((Math.random()-0.5)*6); } return {x,y}
    }
    if(name==='linear'){
    const x=linspace(0,10,n), y=x.map(xx=> 0.9*xx + (Math.random()-0.5)*3); return {x,y}
    }
    if(name==='hist'){
    // draw from a mixture of gaussians
    const x=[], y=[]; for(let i=0;i<n;i++){ const v = (Math.random()<0.6? (Math.random()*1.5+2) : (Math.random()*2+6)); x.push(i); y.push(v + (Math.random()-0.5)*0.4) } return {x,y}
    }
    return {x:[],y:[]}
}

// --- Plotting and UI wiring ---
const plotDiv = document.getElementById('plot');
const datasetEl = document.getElementById('dataset');
const plotTypeEl = document.getElementById('plottype');
const npointsEl = document.getElementById('npoints');
const npointsLabel = document.getElementById('npoints-label');
const smoothingEl = document.getElementById('smoothing');
const trendEl = document.getElementById('trend');
const exportBtn = document.getElementById('exportBtn');

const statN = document.getElementById('stat-n');
const statMean = document.getElementById('stat-mean');
const statMedian = document.getElementById('stat-median');
const statStd = document.getElementById('stat-std');
const statMin = document.getElementById('stat-min');
const statMax = document.getElementById('stat-max');

function updateStats(y){ statN.textContent = y.length; statMean.textContent = mean(y).toFixed(3); statMedian.textContent = median(y).toFixed(3); statStd.textContent = std(y).toFixed(3); statMin.textContent = min(y).toFixed(3); statMax.textContent = max(y).toFixed(3) }

function fitLinear(x,y){ // simple least squares
    const n = x.length; const xm = mean(x); const ym = mean(y);
    let num=0, den=0; for(let i=0;i<n;i++){ num += (x[i]-xm)*(y[i]-ym); den += (x[i]-xm)*(x[i]-xm) }
    const m = num/den; const b = ym - m*xm; const yfit = x.map(xx=> m*xx + b); return {m,b,yfit}
}

function draw(){
    const dataset = datasetEl.value; const ptype = plotTypeEl.value; const n = parseInt(npointsEl.value); npointsLabel.textContent = n;
    const smoothing = parseInt(smoothingEl.value); const showTrend = trendEl.checked;

    const data = generate(dataset,n);
    const x = data.x; let y = data.y.slice();

    // apply smoothing
    const ySm = movingAverage(y,smoothing);

    updateStats(ySm);

    // decide trace type
    let trace;
    if(ptype==='histogram' || dataset==='hist'){
    trace = { x: ySm, type: 'histogram', marker:{opacity:0.8}, autobinx:true };
    } else if(ptype==='bar'){
    trace = { x: x, y: ySm, type: 'bar' };
    } else {
    // scatter or line
    const mode = (ptype==='line')? 'lines' : 'markers+lines';
    trace = { x: x, y: ySm, mode: mode, type: 'scatter', marker:{size:6} };
    }

    const traces = [trace];

    if(showTrend && (ptype!=='histogram')){
    const lf = fitLinear(x,ySm);
    traces.push({ x:x, y:lf.yfit, mode:'lines', line:{dash:'dash', width:2, color:'rgba(0,0,0,0.7)'}, name:'Trend' })
    }

    const layout = {
    margin:{t:36, r:18, l:48, b:36}, hovermode:'closest', legend:{orientation:'h'},
    xaxis:{title: dataset.includes('sine')? 'x (radians)' : (dataset==='hist' ? 'value' : 'x')},
    yaxis:{title: 'y'},
    paper_bgcolor: 'transparent', plot_bgcolor:'#fff'
    }

    Plotly.react(plotDiv, traces, layout, {responsive:true});
}

// initial draw
draw();

// wire events
[datasetEl, plotTypeEl, npointsEl, smoothingEl, trendEl].forEach(el=> el.addEventListener('input', draw));

exportBtn.addEventListener('click', ()=>{
    Plotly.toImage(plotDiv, {format:'png', height:600, width:900}).then(url=>{
    const a=document.createElement('a'); a.href=url; a.download='plot.png'; document.body.appendChild(a); a.click(); a.remove();
    })
})

// improve UX: when dataset is histogram force histogram plot type
datasetEl.addEventListener('change', ()=>{
    if(datasetEl.value==='hist') plotTypeEl.value='histogram';
    draw();
})