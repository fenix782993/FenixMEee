(function(){
const app=document.getElementById('app'); if(!app) return;
const old=window.fenixPhoneAuth;
window.fenixPhoneAuth={
  render(){
    app.innerHTML=`<div class="auth"><div class="authcard phone-auth-card">
      <div class="authlogo">✈</div><h1>Fenix Messenger</h1><p>Регистрация и вход по номеру телефона</p>
      <div id="pa-error" class="error hidden"></div><div id="pa-step"></div>
    </div></div>`; this.stepPhone();
  },
  stepPhone(){const s=document.getElementById('pa-step'); s.innerHTML=`<form class="form" id="pa-form">
    <label>Номер телефона</label><input id="pa-phone" type="tel" inputmode="tel" placeholder="+49 170 1234567" autocomplete="tel" required>
    <div class="pa-actions"><button class="primary" type="submit">Продолжить</button></div>
    <small>Мы отправим SMS с кодом подтверждения.</small></form>`;
    document.getElementById('pa-form').onsubmit=e=>{e.preventDefault(); this.request(document.getElementById('pa-phone').value,'register')};
  },
  async request(phone,purpose){try{const d=await this.api('/api/auth/phone/request',{method:'POST',body:JSON.stringify({phone,purpose})});localStorage.setItem('fenix_pending_phone',d.phone);localStorage.setItem('fenix_pending_purpose',purpose);this.stepCode(d.phone,purpose)}catch(e){this.err(e.message)}},
  stepCode(phone,purpose){const s=document.getElementById('pa-step'); s.innerHTML=`<form class="form" id="pa-code-form"><label>Код из SMS</label><input id="pa-code" inputmode="numeric" maxlength="6" placeholder="123456" autocomplete="one-time-code" required><button class="primary">Подтвердить</button><button type="button" class="secondary" id="pa-back">Изменить номер</button><small>Код действует 5 минут.</small></form>`;document.getElementById('pa-code-form').onsubmit=e=>{e.preventDefault();this.verify(phone,purpose,document.getElementById('pa-code').value)};document.getElementById('pa-back').onclick=()=>this.stepPhone()},
  async verify(phone,purpose,code){try{const d=await this.api('/api/auth/phone/verify',{method:'POST',body:JSON.stringify({phone,purpose,code})});if(d.status==='authenticated'){localStorage.setItem('fenix_token',d.access_token);location.reload();return}this.stepProfile(phone,d.signup_token)}catch(e){this.err(e.message)}},
  stepProfile(phone,signup){const s=document.getElementById('pa-step');s.innerHTML=`<form class="form" id="pa-profile"><div class="avatar-upload"><div id="pa-avatar-preview" class="big-avatar">+</div><input id="pa-avatar" type="file" accept="image/*"></div><label>Имя</label><input id="pa-name" maxlength="80" placeholder="Ваше имя" required><label>Username</label><input id="pa-user" minlength="5" maxlength="32" pattern="[A-Za-z0-9_]+" placeholder="username" required><small>Минимум 5 символов. По нему вас смогут найти.</small><button class="primary">Готово</button></form>`;let avatar='';document.getElementById('pa-avatar').onchange=async e=>{const f=e.target.files[0];if(!f)return;const url=URL.createObjectURL(f);document.getElementById('pa-avatar-preview').style.backgroundImage=`url(${url})`;document.getElementById('pa-avatar-preview').textContent='';avatar=f};document.getElementById('pa-profile').onsubmit=async e=>{e.preventDefault();try{let av=null;if(avatar){av=await this.uploadBeforeAuth(avatar)}const d=await this.api('/api/auth/phone/complete?signup_token='+encodeURIComponent(signup),{method:'POST',body:JSON.stringify({username:document.getElementById('pa-user').value,display_name:document.getElementById('pa-name').value,avatar:av})});localStorage.setItem('fenix_token',d.access_token);location.reload()}catch(x){this.err(x.message)}}},
  async uploadBeforeAuth(file){const fd=new FormData();fd.append('file',file);const r=await fetch('/api/public/avatar',{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось загрузить аватар');return d.url},
  err(m){const e=document.getElementById('pa-error');e.textContent=m;e.classList.remove('hidden')},
  async api(p,o={}){const r=await fetch(p,{headers:{'Content-Type':'application/json',...(o.headers||{})},...o});let d;try{d=await r.json()}catch{d={detail:'Ошибка сервера'}}if(!r.ok)throw new Error(d.detail||'Ошибка');return d}
}; window.fenixPhoneAuth.render();
})();
