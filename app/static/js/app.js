'use strict';
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('details').forEach(detail=>{if(detail.querySelector('.errorlist,.field-error'))detail.open=true;});
  document.querySelectorAll('[data-confirm]').forEach(form=>form.addEventListener('submit',event=>{
    if(!window.confirm(form.dataset.confirm))event.preventDefault();
  }));
  document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
    const input=document.getElementById(button.dataset.copy);if(!input)return;
    try{await navigator.clipboard.writeText(input.value);button.textContent='Copied';}
    catch{input.focus();input.select();button.textContent='Select and copy this link';}
  }));
  const availability=document.querySelector('[data-availability-form]');
  if(availability){
    const kind=availability.querySelector('[name=kind]'),day=availability.querySelector('[name=weekday]'),date=availability.querySelector('[name=date]');
    const update=()=>{day.closest('.field').hidden=kind.value!=='weekly';date.closest('.field').hidden=kind.value!=='date';};
    kind.addEventListener('change',update);update();
  }
  document.querySelectorAll('input[type=password]').forEach(input=>{
    const toggle=document.createElement('button');toggle.type='button';toggle.className='password-toggle';toggle.textContent='Show password';toggle.setAttribute('aria-controls',input.id);toggle.setAttribute('aria-pressed','false');
    toggle.addEventListener('click',()=>{const show=input.type==='password';input.type=show?'text':'password';toggle.textContent=show?'Hide password':'Show password';toggle.setAttribute('aria-pressed',String(show));});input.insertAdjacentElement('afterend',toggle);
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)){
      const search=document.querySelector('[data-search]');if(search){event.preventDefault();search.focus();}
    }
  });
});
