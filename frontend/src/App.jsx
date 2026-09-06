import { useEffect } from 'react';

export default function App(){
  useEffect(()=>{
    // Production is served from frontend/dist by FastAPI Cloud.
    // Keep this source entry intentionally minimal; the deployment bundle is the
    // fully interactive vanilla client in dist/assets/app.js.
  },[]);
  return null;
}
