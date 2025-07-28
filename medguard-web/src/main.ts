import './style.css'

import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'

// i18n setup
const messages = {
  'en-ZA': {
    dashboard: {
      title: 'Medication Dashboard',
      subtitle: 'Manage your medications safely',
      todaySchedule: 'Today\'s Schedule',
      medicationList: 'Medication List',
      stockAlerts: 'Stock Alerts',
      addMedication: 'Add Medication',
      taken: 'Taken',
      missed: 'Missed',
      upcoming: 'Upcoming',
      lowStock: 'Low Stock',
      outOfStock: 'Out of Stock',
      pillsRemaining: 'pills remaining',
      noMedications: 'No medications scheduled',
      noAlerts: 'No stock alerts',
      markAsTaken: 'Mark as Taken',
      markAsMissed: 'Mark as Missed',
      editMedication: 'Edit',
      deleteMedication: 'Delete',
      refillReminder: 'Refill Reminder',
      dosage: 'Dosage',
      frequency: 'Frequency',
      time: 'Time',
      status: 'Status'
    },
    common: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      close: 'Close',
      yes: 'Yes',
      no: 'No',
      confirm: 'Confirm'
    }
  },
  'af-ZA': {
    dashboard: {
      title: 'Medikasie Dashboard',
      subtitle: 'Bestuur jou medikasie veilig',
      todaySchedule: 'Vandag se Skedule',
      medicationList: 'Medikasie Lys',
      stockAlerts: 'Voorraad Waarskuwings',
      addMedication: 'Voeg Medikasie By',
      taken: 'Geneem',
      missed: 'Gemis',
      upcoming: 'Komende',
      lowStock: 'Lae Voorraad',
      outOfStock: 'Uit Voorraad',
      pillsRemaining: 'pille oor',
      noMedications: 'Geen medikasie geskeduleer',
      noAlerts: 'Geen voorraad waarskuwings',
      markAsTaken: 'Merk as Geneem',
      markAsMissed: 'Merk as Gemis',
      editMedication: 'Redigeer',
      deleteMedication: 'Verwyder',
      refillReminder: 'Hervul Herinnering',
      dosage: 'Dosis',
      frequency: 'Frekwensie',
      time: 'Tyd',
      status: 'Status'
    },
    common: {
      loading: 'Laai...',
      error: 'Fout',
      success: 'Sukses',
      cancel: 'Kanselleer',
      save: 'Stoor',
      delete: 'Verwyder',
      edit: 'Redigeer',
      add: 'Voeg By',
      close: 'Sluit',
      yes: 'Ja',
      no: 'Nee',
      confirm: 'Bevestig'
    }
  }
}

const i18n = createI18n({
  legacy: false,
  locale: 'en-ZA',
  fallbackLocale: 'en-ZA',
  messages
})

const app = createApp(App)
app.use(i18n)
app.mount('#app')
