import {createRoot} from 'react-dom/client'
import './index.css'
import App from './App'
import {I18n} from './i18n'
createRoot(document.getElementById('root')!).render(<I18n><App/></I18n>)
