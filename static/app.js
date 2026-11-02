document.addEventListener('DOMContentLoaded',()=>{
  const sb=document.querySelector('.sidebar'),bg=document.querySelector('.burger');
  if(bg&&sb)bg.addEventListener('click',()=>sb.classList.toggle('open'));
  // syllabus tabs
  document.querySelectorAll('.syl-tabs button').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('.syl-tabs button,.syl').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');document.getElementById(b.dataset.t).classList.add('on');}));
  // carousel
  const tr=document.querySelector('.track');
  if(tr){let i=0;const n=tr.children.length,dots=document.querySelectorAll('.cnav i.d');
    const go=k=>{i=(k+n)%n;tr.style.transform='translateX(-'+i*100+'%)';dots.forEach((d,j)=>d.classList.toggle('on',j===i));};
    document.getElementById('cprev')?.addEventListener('click',()=>go(i-1));document.getElementById('cnext')?.addEventListener('click',()=>go(i+1));
    setInterval(()=>go(i+1),5000);go(0);}
  // login role tabs / quick login
  window.setRole=(r,el)=>{document.querySelectorAll('.rtab').forEach(t=>t.classList.remove('on'));el.classList.add('on');document.getElementById('uname').value=r;};
  window.qLogin=(u,p)=>{document.getElementById('uname').value=u;document.getElementById('pw').value=p;document.getElementById('lf').submit();};
  // attendance quick buttons
  window.markAll=v=>document.querySelectorAll('.att-select').forEach(s=>s.value=v);
  // fee type -> amount autofill
  const ft=document.getElementById('fee_type');
  if(ft)ft.addEventListener('change',()=>{document.getElementById('fee_amount').value=ft.selectedOptions[0].dataset.amt||'';});
  // grade suggestion
  const mo=document.getElementById('marks_obtained'),mx=document.getElementById('max_marks'),gr=document.getElementById('grade');
  const sug=()=>{if(!mo||!gr)return;const p=mx.value?mo.value/mx.value*100:0;gr.value=p>=90?'O':p>=80?'A+':p>=70?'A':p>=60?'B':p>=50?'C':'F';};
  mo&&mo.addEventListener('input',sug);mx&&mx.addEventListener('input',sug);
  // dropzone
  const dz=document.querySelector('.dropzone'),fi=document.getElementById('material_file');
  if(dz&&fi){dz.addEventListener('click',()=>fi.click());
    ['dragover','dragenter'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.add('over')}));
    ['dragleave','drop'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.remove('over')}));
    dz.addEventListener('drop',ev=>{fi.files=ev.dataTransfer.files;dz.querySelector('span').textContent=fi.files[0].name;});
    fi.addEventListener('change',()=>{if(fi.files[0])dz.querySelector('span').textContent=fi.files[0].name;});}
  // login-account toggle
  const cl=document.getElementById('create_login');
  if(cl)cl.addEventListener('change',()=>document.getElementById('login_box').style.display=cl.checked?'block':'none');
  // confirm deletes
  document.querySelectorAll('[data-confirm]').forEach(a=>a.addEventListener('click',e=>{if(!confirm(a.dataset.confirm))e.preventDefault();}));
});
