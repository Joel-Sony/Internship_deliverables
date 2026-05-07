# Week 13 React Concepts Guide

This guide breaks down the core React concepts that were implemented in your Week 13 Dashboard project. It's designed to explain both **how** they are used in your code and the **theory** behind why you need them.

---

## 1. Functional Components

### Theory
In React, a component is a reusable piece of the UI. You can think of components as custom HTML elements or JavaScript functions that return UI markup (JSX). There are two main types of components: Class components (older) and Functional components (modern). Your dashboard uses entirely **Functional Components**.

### Implementation in your Code
Look at `StatCard.jsx` and `App.jsx`. Each of these files defines a JavaScript function that returns some HTML-like syntax called JSX.

```jsx
// From StatCard.jsx
function StatCard({ label, value, change, trend }) {
    return (
        <div className="card">
            <p className="stat-label">{label}</p>
            {/* ... */}
        </div>
    );
}
export default StatCard;
```

By exporting `StatCard`, you can import it into `App.jsx` and use it as if it were a built-in HTML tag: `<StatCard />`.

---

## 2. Props (Properties)

### Theory
Props are how you pass data from a parent component down to a child component. They are read-only (immutable) from the child's perspective. Think of them like arguments passed into a normal JavaScript function.

### Implementation in your Code
In `App.jsx`, you pass an array of data into the `RecentItems` component:

```jsx
// App.jsx (Parent)
<RecentItems items={activityData} />
```

Then, in `RecentItems.jsx`, the component "receives" the props. Notice how it uses object destructuring `{ items }` to pull out the `items` property directly from the props object:

```jsx
// RecentItems.jsx (Child)
function RecentItems({ items }) {
    // items is now the activityData array passed from App.jsx
    // ...
}
```

---

## 3. Rendering Lists with `.map()`

### Theory
When you have an array of data, you don't want to manually code each item on the screen. Instead, React uses standard JavaScript array methods, specifically `.map()`, to transform an array of data into an array of JSX elements.

> **Crucial Rule:** Every item in a mapped React list MUST have a unique `key` prop. This helps React figure out exactly which items changed, were added, or were removed, optimizing performance.

### Implementation in your Code
In `App.jsx`, you render multiple `StatCard`s using `.map()`:

```jsx
<div className="stats-grid">
  {statsData.map(s => <StatCard key={s.label} {...s} />)}
</div>
```
You used `s.label` as the unique `key` because every stat card ("Total Users", "Revenue", etc.) has a different label.

In `Announcements.jsx`:
```jsx
{items.map(ann => (
    <AnnouncementItem key={ann.id} {...ann} />
))}
```
Here, you used the database `id` as the key, which is the most reliable best practice for keys.

---

## 4. Spread Operator (`...`) for Props

### Theory
Sometimes an object has exact property names that match the prop names a component is expecting. Instead of passing them one by one (`label={s.label} value={s.value} change={s.change}`), you can use the JavaScript ES6 spread operator `...` to pass all properties of the object as individual props.

### Implementation in your Code
Your `statsData` array contains objects like this:
`{ label: 'Total Users', value: '12,480', change: '▲ 8.2%', trend: 'up' }`

Instead of doing this:
```jsx
<StatCard 
  label={s.label} 
  value={s.value} 
  change={s.change} 
  trend={s.trend} 
/>
```

You elegantly "spread" the object properties directly into the component:
```jsx
<StatCard key={s.label} {...s} />
```
Because the properties on the data object perfectly match the destructuring arguments expected by `function StatCard({ label, value, change, trend })`, everything lines up perfectly.

---

## 5. Dynamic Class Names (Template Literals)

### Theory
In plain HTML, class names are static strings (`class="btn btn-primary"`). In React, because we are using JSX inside JavaScript, we can use JavaScript's logic to dynamically construct class names based on our data. We usually use JS Template Literals (`` `string ${variable}` ``) for this.

### Implementation in your Code
In `StatCard.jsx`, the text color of the stat change (up or down trend) needs to change dynamically:

```jsx
<span className={`stat-change ${trend}`}>
    {change}
</span>
```
If `trend` is `'up'`, the class becomes `"stat-change up"`. If it's `'down'`, it becomes `"stat-change down"`. 

You did an even more advanced version of this in `RecentItems.jsx` by calling a method inside the literal:
```jsx
<span className={`status-badge status-${item.status.toLowerCase()}`}>
```
If `item.status` is `'Done'`, it computes to `"status-badge status-done"`, mapping cleanly to your CSS rules.

---

## Summary of your progress
Your Week 13 code shows a very strong grasp of foundational React:
1. You successfully broke a large UI into modular, single-responsibility **components** (`StatCard`, `RecentItems`, `Announcements`).
2. You successfully separated your **data** from your **view** (data is declared at the top of App.jsx, keeping the JSX clean).
3. You dynamically generated UI from arrays using `.map()`.
4. You applied dynamic styling based on the state of the data. 

To take this to the next level in future weeks, you'll start looking into **State** (`useState`) and **Effects** (`useEffect`) to make these components interactive and fetch this data from an external backend API instead of hardcoding it!
