import {useEffect,useState} from 'react';import {get} from '../lib/api';
export function useAuth(){const [me,setMe]=useState(null),[loading,setLoading]=useState(true);useEffect(()=>{if(!localStorage.getItem('fenix_token')){setLoading(false);return}get('/api/users/me').then(setMe).catch(()=>localStorage.removeItem('fenix_token')).finally(()=>setLoading(false))},[]);return{me,setMe,loading}}
