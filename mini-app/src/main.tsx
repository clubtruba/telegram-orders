import React, { useEffect, useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { api } from './api/client'
import { initializeTelegram } from './telegram'
import type { AuthMe, Customer, Dashboard, Item } from './types'
import './style.css'

type View = 'home'|'items'|'warehouse'|'customers'|'profile'
const labels:Record<string,string> = {TO_BUY:'Нужно купить',ORDERED:'Заказано',PURCHASED_OFFLINE:'Куплено офлайн',ON_THE_WAY_TO_US:'Едет к нам',READY_FOR_PICKUP:'Ждёт получения',RECEIVED:'Получено',ASSIGNED_TO_SHIPMENT:'Готовится к отправке',SHIPPED:'Отправлено',DELIVERED:'Доставлено',CANCELLED:'Отменено',RETURN_IN_PROGRESS:'Возврат',RETURNED:'Возвращено'}

function App() {
  const initData = useMemo(initializeTelegram, [])
  const [me,setMe] = useState<AuthMe|null>(null), [dashboard,setDashboard] = useState<Dashboard|null>(null)
  const [items,setItems] = useState<Item[]>([]), [customers,setCustomers] = useState<Customer[]>([])
  const [view,setView] = useState<View>('home'), [loading,setLoading] = useState(true)
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
  const navigation:{id:View;label:string}[]=admin?[{id:'home',label:'Главная'},{id:'items',label:'Заказы'},{id:'warehouse',label:'Склад'},{id:'customers',label:'Клиенты'}]:[{id:'home',label:'Главная'},{id:'items',label:'Мои товары'},{id:'profile',label:'Профиль'}]
  const visibleItems=view==='warehouse'?items.filter(i=>['RECEIVED','ASSIGNED_TO_SHIPMENT'].includes(i.status)):items
  return <div className="app-shell"><header><p className="eyebrow">TELEGRAM ORDERS</p><h1>{admin?'Управление заказами':'Мои заказы'}</h1></header><main>
    {view==='home'&&<DashboardView data={dashboard} admin={admin}/>} {(view==='items'||view==='warehouse')&&<ItemsView items={visibleItems}/>} {view==='customers'&&<CustomersView customers={customers}/>} {view==='profile'&&<section className="card"><h2>Профиль</h2><p>Адреса и настройки уведомлений появятся здесь.</p></section>}
  </main><nav>{navigation.map(i=><button key={i.id} className={view===i.id?'active':''} onClick={()=>setView(i.id)}>{i.label}</button>)}</nav></div>
}
function DashboardView({data,admin}:{data:Dashboard;admin:boolean}) {const metrics=[['Нужно купить',data.to_buy],['Едет к нам',data.on_the_way],['Получено',data.received],[admin?'В посылках':'Готовится',data.assigned_to_shipment]];return <><section className="metrics">{metrics.map(([label,value])=><article className="metric" key={label}><strong>{value}</strong><span>{label}</span></article>)}</section><section className="card"><h2>{admin?'Требует внимания':'Статус отправки'}</h2><p>{data.received?`${data.received} товар(а) уже получено.`:'Полученных товаров пока нет.'}</p></section></>}
function ItemsView({items}:{items:Item[]}) {if(!items.length)return <State title="Здесь пока пусто" text="Новые товары появятся после отправки ссылки боту."/>;return <section className="list">{items.map(item=><article className="item" key={item.id}><div><h2>{new URL(item.product_url).hostname.replace('www.','')}</h2><p>{[item.size&&`Размер ${item.size}`,item.color].filter(Boolean).join(' · ')||'Без параметров'}</p></div><span className={`status status-${item.status.toLowerCase()}`}>{labels[item.status]??item.status}</span></article>)}</section>}
function CustomersView({customers}:{customers:Customer[]}) {if(!customers.length)return <State title="Клиентов пока нет"/>;return <section className="list">{customers.map(c=><article className="item" key={c.id}><div><h2>{c.display_name}</h2><p>{c.phone??'Телефон не указан'}</p></div><span className="status">{c.collection_status}</span></article>)}</section>}
function State({title,text}:{title:string;text?:string}) {return <main className="state"><div><p className="eyebrow">TELEGRAM ORDERS</p><h1>{title}</h1>{text&&<p>{text}</p>}</div></main>}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
