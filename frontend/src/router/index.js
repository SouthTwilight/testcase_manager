import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/test-cases',
        name: 'TestCases',
        component: () => import('../views/TestCases.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/test-plans',
        name: 'TestPlans',
        component: () => import('../views/TestPlans.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/execution-history',
        name: 'ExecutionHistory',
        component: () => import('../views/ExecutionHistory.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/machines',
        name: 'Machines',
        component: () => import('../views/Machines.vue'),
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
