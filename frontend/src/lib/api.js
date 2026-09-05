export const API=import.meta.env.VITE_API_URL||'';
export function token(){return localStorage.getItem('fenix_token')||''}
export async function request(path,options={}){const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(options.headers||{})};if(token())headers.Authorization=`Bearer ${token()}`;const r=await fetch(`${API}${path}`,{...options,headers});if(!r.ok){let e={};try{e=await r.json()}catch{}throw new Error(e.detail||`HTTP ${r.status}`)}return r.status===204?null:r.json()}
export const get=(p)=>request(p);export const post=(p,b)=>request(p,{method:'POST',body:b instanceof FormData?b:JSON.stringify(b)});export const patch=(p,b)=>request(p,{method:'PATCH',body:JSON.stringify(b)});export const del=(p)=>request(p,{method:'DELETE'});
