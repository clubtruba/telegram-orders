import React, { useEffect, useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { api } from './api/client'
import { initializeTelegram } from './telegram'
import type { AuthMe, Customer, Dashboard, Item, ItemStatus } from './types'
import './style.css'

type View = 'home'|'items'|'warehouse'|'customers'|'profile'
const labels:Record<string,string> = {TO_BUY:'Нужно купить',ORDERED:'Заказано',PURCHASED_OFFLINE:'Куплено офлайн',ON_THE_WAY_TO_US:'Едет к нам',READY_FOR_PICKUP:'Ждёт получения',RECEIVED:'Получено',ASSIGNED_TO_SHIPMENT:'Готовится к отправке',SHIPPED:'Отправлено',DELIVERED:'Доставлено',CANCELLED:'Отменено',RETURN_IN_PROGRESS:'Возврат',RETURNED:'Возвращено'}
const transitions:Record<ItemStatus,ItemStatus[]>={TO_BUY:['ORDERED','PURCHASED_OFFLINE','CANCELLED'],ORDERED:['ON_THE_WAY_TO_US','READY_FOR_PICKUP','CANCELLED'],PURCHASED_OFFLINE:['RECEIVED','RETURN_IN_PROGRESS'],ON_THE_WAY_TO_US:['READY_FOR_PICKUP','RECEIVED','RETURN_IN_PROGRESS'],READY_FOR_PICKUP:['RECEIVED','RETURN_IN_PROGRESS'],RECEIVED:['ASSIGNED_TO_SHIPMENT','RETURN_IN_PROGRESS'],ASSIGNED_TO_SHIPMENT:['RECEIVED','SHIPPED'],SHIPPED:['DELIVERED'],RETURN_IN_PROGRESS:['RETURNED','RECEIVED'],DELIVERED:[],CANCELLED:[],RETURNED:[]}

function App() {
  const initData = useMemo(initializeTelegram, [])
  const [me,setMe] = useState<AuthMe|null>(null), [dashboard,setDashboard] = useState<Dashboard|null>(null)
  const [items,setItems] = useState<Item[]>([]), [customers,setCustomers] = useState<Customer[]>([])
  const [view,setView] = useState<View>('home'), [loading,setLoading] = useState(true)
  const [updating,setUpdating] = useState<string|null>(null)
  const [error,setError] = useState<string|null>(null)
  useEffect(()=>{
    if(!initData){setError('Откройте приложение из личного чата с Telegram-ботом.');setLoading(false);return}
    Promise.all([api.me(initData),api.dashboard(initData),api.items(initData)])
      .then(([identity,summary,itemList])=>{setMe(identity);setDashboard(summary);setItems(itemList)})
      .catch((reason:Error)=>setError(reason.message)).finally(()=>setLoading(false))
  },[initData])
  useEffect(()=>{
    if(!me||me.role!=='ADMIN'||view!=='customers'||customers.length)return
    api.customers(initData).then(setCustomers).catch((reason:Error)=>setError(reason.message))
  },[customers.length,initData,me,view])
  if(loading)return <State title="Загружаем заказы…" />
  if(error||!me||!dashboard)return <State title="Не удалось открыть приложение" text={error??'Нет данных пользователя'} />
  const admin=me.role==='ADMIN'
  const updateStatus=async(item:Item,target:ItemStatus)=>{setUpdating(item.id);setError(null);try{const updated=await api.updateItemStatus(initData,item.id,target);setItems(current=>current.map(value=>value.id===updated.id?updated:value));setDashboard(await api.dashboard(initData))}catch(reason){setError(reason instanceof Error?reason.message:'Не удалось изменить статус')}finally{setUpdating(null)}}
  const navigation:{id:View;label:string}[]=admin?[{id:'home',label:'Главная'},{id:'items',label:'Заказы'},{id:'warehouse',label:'Склад'},{id:'customers',label:'Клиенты'}]:[{id:'home',label:'Главная'},{id:'items',label:'Мои товары'},{id:'profile',label:'Профиль'}]
  const visibleItems=view==='warehouse'?items.filter(i=>['RECEIVED','ASSIGNED_TO_SHIPMENT'].includes(i.status)):items
  return <div className="app-shell"><header><p className="eyebrow">TELEGRAM ORDERS</p><h1>{admin?'Управление заказами':'Мои заказы'}</h1></header><main>
    {view==='home'&&<DashboardView data={dashboard} admin={admin}/>} {(view==='items'||view==='warehouse')&&<ItemsView items={visibleItems} admin={admin} updating={updating} onTransition={updateStatus}/>} {view==='customers'&&<CustomersView customers={customers}/>} {view==='profile'&&<section className="card"><h2>Профиль</h2><p>Адреса и настройки уведомлений появятся здесь.</p></section>}
  </main><nav>{navigation.map(i=><button key={i.id} className={view===i.id?'active':''} onClick={()=>setView(i.id)}>{i.label}</button>)}</nav></div>
}
function DashboardView({data,admin}:{data:Dashboard;admin:boolean}) {const metrics=[['Нужно купить',data.to_buy],['Едет к нам',data.on_the_way],['Получено',data.received],[admin?'В посылках':'Готовится',data.assigned_to_shipment]];return <><section className="metrics">{metrics.map(([label,value])=><article className="metric" key={label}><strong>{value}</strong><span>{label}</span></article>)}</section><section className="card"><h2>{admin?'Требует внимания':'Статус отправки'}</h2><p>{data.received?`${data.received} товар(а) уже получено.`:'Полученных товаров пока нет.'}</p></section></>}
function ItemsView({items,admin,updating,onTransition}:{items:Item[];admin:boolean;updating:string|null;onTransition:(item:Item,target:ItemStatus)=>void}) {if(!items.length)return <State title="Здесь пока пусто" text="Новые товары появятся после отправки ссылки боту."/>;return <section className="list">{items.map(item=><article className="item item-manage" key={item.id}><div><h2>{new URL(item.product_url).hostname.replace('www.','')}</h2><p>{[item.size&&`Размер ${item.size}`,item.color].filter(Boolean).join(' · ')||'Без параметров'}</p></div><div className="item-actions"><span className={`status status-${item.status.toLowerCase()}`}>{labels[item.status]??item.status}</span>{admin&&transitions[item.status].length>0&&<select aria-label="Изменить статус" disabled={updating===item.id} value="" onChange={event=>onTransition(item,event.target.value as ItemStatus)}><option value="" disabled>{updating===item.id?'Сохраняем…':'Изменить статус'}</option>{transitions[item.status].map(target=><option value={target} key={target}>{labels[target]}</option>)}</select>}</div></article>)}</section>}
function CustomersView({customers}:{customers:Customer[]}) {if(!customers.length)return <State title="Клиентов пока нет"/>;return <section className="list">{customers.map(c=><article className="item" key={c.id}><div><h2>{c.display_name}</h2><p>{c.phone??'Телефон не указан'}</p></div><span className="status">{c.collection_status}</span></article>)}</section>}
function State({title,text}:{title:string;text?:string}) {return <main className="state"><div><p className="eyebrow">TELEGRAM ORDERS</p><h1>{title}</h1>{text&&<p>{text}</p>}</div></main>}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
