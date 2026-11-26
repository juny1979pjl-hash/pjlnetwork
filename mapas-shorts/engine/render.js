const {chromium}=require('playwright');const http=require('http');const fs=require('fs');const path=require('path');const {spawn}=require('child_process');
const root=__dirname;const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{const f=path.join(root,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':mime[path.extname(f)]||'application/octet-stream'});r.end(d)})}).listen(8765);
(async()=>{
  const mode=process.argv[2]||'preview';
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('pageerror',e=>console.error('PAGEERR',e.message));
  await p.goto('http://localhost:8765/page.html');
  const scenes=JSON.parse(fs.readFileSync('scenes.json'));const durs=JSON.parse(fs.readFileSync('durs.json'));
  const total=await p.evaluate(([s,d])=>init(s,d),[scenes,durs]);
  const el=await p.$('canvas');
  if(mode==='preview'){
    let t=0;const T=durs.map(d=>{const s=t;t+=d;return s});
    for(let i=0;i<T.length;i++){const tt=T[i]+durs[i]*0.85;await p.evaluate(x=>draw(x),tt);await el.screenshot({path:`prev${i}.jpg`,type:'jpeg',quality:70});}
  } else {
    const fps=30,N=Math.ceil(total*fps);
    const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',''+fps,'-c:v','mjpeg','-i','-','-i','voice.wav','-c:v','libx264','-pix_fmt','yuv420p','-preset','medium','-crf','20','-c:a','aac','-b:a','192k','-shortest',process.argv[3]||'short.mp4'],{stdio:['pipe','inherit','inherit']});
    for(let f=0;f<N;f++){
      const b64=await p.evaluate(x=>{draw(x);return document.getElementById('c').toDataURL('image/jpeg',0.92).split(',')[1]},f/fps);
      const buf=Buffer.from(b64,'base64');if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
      if(f%150===0)console.log('frame',f,'/',N);
    }
    ff.stdin.end();await new Promise(r=>ff.on('close',r));
  }
  await b.close();srv.close();
})();
