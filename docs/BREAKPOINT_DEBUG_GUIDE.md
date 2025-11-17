# Breakpoint Debug Guide - Dog Details Issue

## Where to Set Breakpoints

### 1. Primary Breakpoint (Highest Leverage)
**File**: `services/webapp-react/src/hooks/useDogDetails.js`  
**Line**: **41** (right after `await getDogById(id)`)

```javascript
const result = await getDogById(id);  // <- SET BREAKPOINT HERE

// 🔍 BREAKPOINT TARGET: Inspect `result` here
console.log('🔍 [useDogDetails] BREAKPOINT CHECKPOINT - Result received:', {...});
```

**What to inspect:**
- `result` object structure
- `result.success` (should be `true`)
- `result.data` (should be the normalized dog object)
- `result.error` (should be `undefined`)

**If breakpoint never hits:**
- Code version mismatch (caching/hot-reload issue)
- Hard refresh browser (Cmd+Shift+R)
- Check DevTools Sources tab for actual code running
- Restart `npm run dev` if needed

**If breakpoint hits:**
- Inspect `result` in Scope panel
- Step over to next line
- Verify `result.success === true` and `result.data` exists

---

### 2. Secondary Breakpoint (Before setDog)
**File**: `services/webapp-react/src/hooks/useDogDetails.js`  
**Line**: **74** (right before `setDog(result.data)`)

```javascript
// 🔍 BREAKPOINT TARGET: Inspect before setDog
console.log('🔍 [useDogDetails] About to call setDog with:', {...});
setDog(result.data);  // <- SET BREAKPOINT HERE
```

**What to inspect:**
- `result.data` structure
- `result.data.Name` (should be dog name)
- `result.data.id` (should be dog ID)
- Verify data looks correct before state update

---

### 3. Repository Breakpoint (Verify Return Value)
**File**: `services/webapp-react/src/repositories/dogRepository.js`  
**Line**: **81** (right before `return result`)

```javascript
// 🔍 BREAKPOINT TARGET: Inspect return value here
console.log('🔍 [getDogById] BREAKPOINT CHECKPOINT - Returning result:', {...});
return result;  // <- SET BREAKPOINT HERE
```

**What to inspect:**
- `result` structure matches expected format
- `result.success === true`
- `result.data` contains normalized dog
- Compare with what hook receives

---

### 4. Component Breakpoint (Verify Hook Return)
**File**: `services/webapp-react/src/pages/DogDetails.jsx`  
**Line**: **160** (right after `useDogDetails(id)`)

```javascript
const { dog, loading, error } = useDogDetails(id);  // <- SET BREAKPOINT HERE

// 🔍 BREAKPOINT CHECKPOINT: Verify hook state after each render
console.log('🔍 [DogDetails] BREAKPOINT CHECKPOINT - Hook state:', {...});
```

**What to inspect:**
- `dog` state value (should be non-null after fetch)
- `loading` state (should be `false` after fetch)
- `error` state (should be `null` on success)
- React DevTools Components tab to verify prop values

---

## Debugging Flow

### Step 1: Verify Code Version
1. Open DevTools → Sources tab
2. Search for `"BREAKPOINT CHECKPOINT"` in bundled code
3. If not found → hard refresh (Cmd+Shift+R) or restart dev server

### Step 2: Set Primary Breakpoint
1. Set breakpoint at line 41 in `useDogDetails.js`
2. Navigate to `/dog/212143233` (or any dog ID)
3. **If breakpoint doesn't hit** → caching issue, see above
4. **If breakpoint hits** → proceed to Step 3

### Step 3: Inspect Result Object
1. When paused at breakpoint, inspect `result` in Scope panel
2. Check:
   - `result.success` === `true`?
   - `result.data` exists and has `Name` property?
   - `result.data.id` matches the route parameter?
3. If `result` is wrong → check `getDogById` return value (set breakpoint at line 81)

### Step 4: Step Through State Update
1. Step over to line 74 (before `setDog`)
2. Verify `result.data` still looks correct
3. Step over `setDog(result.data)`
4. Check React DevTools → Components → `DogDetails` → verify `dog` prop updated

### Step 5: Verify Render
1. Continue execution
2. Check console for `🔍 [DogDetails] BREAKPOINT CHECKPOINT - Hook state:`
3. Verify `hasDog: true` in the log
4. If `hasDog: false` → state update didn't work (React issue)

---

## Expected Console Output (Success Case)

```
[useDogDetails] Fetching dog with ID: 212143233
[getDogById] Looking up dog document with ID: 212143233
[getDogById] Document exists: true ID: 212143233
[getDogById] Normalizing dog document...
[getDogById] Normalization successful, dog name: Tasha 13501
🔍 [getDogById] BREAKPOINT CHECKPOINT - Returning result: {...}
🔍 [useDogDetails] BREAKPOINT CHECKPOINT - Result received: {...}
[useDogDetails] Component still mounted, processing result
🔍 [useDogDetails] About to call setDog with: {...}
✅ [useDogDetails] setDog called successfully
[useDogDetails] Setting loading to false
🔍 [DogDetails] BREAKPOINT CHECKPOINT - Hook state: { hasDog: true, ... }
```

---

## Common Issues & Solutions

### Issue: Breakpoint Never Hits
**Cause**: Code version mismatch  
**Solution**: 
- Hard refresh browser (Cmd+Shift+R)
- Check Network tab → "Disable cache"
- Restart dev server
- Verify Sources tab shows updated code

### Issue: `result` is `undefined`
**Cause**: `getDogById` not returning expected value  
**Solution**: 
- Set breakpoint in `getDogById` at return statement
- Verify return value structure
- Check for silent exceptions

### Issue: `result.success === false`
**Cause**: Error occurred in `getDogById`  
**Solution**: 
- Check `result.error` object
- Look for error logs before breakpoint
- Verify Firestore document exists (use CLI tool)

### Issue: `setDog` Called But `dog` Still Null
**Cause**: React state update issue or component unmount  
**Solution**: 
- Check React DevTools for actual state
- Verify component didn't unmount (check `isMountedRef`)
- Check for React StrictMode double-invocation
- Verify no other code is resetting `dog` state

### Issue: `hasDog: false` After `setDog`
**Cause**: State update not triggering re-render  
**Solution**: 
- Check React DevTools Components tab
- Verify `dog` prop value in component tree
- Check for conditional rendering logic issues
- Verify no early returns preventing render

---

## Quick Checklist

- [ ] Breakpoint hits at line 41
- [ ] `result.success === true`
- [ ] `result.data` exists and has `Name` property
- [ ] `setDog(result.data)` executes
- [ ] React DevTools shows `dog` prop updated
- [ ] Component re-renders with `hasDog: true`
- [ ] `DogContent` component renders (not `DogNotFoundState`)

---

## Files Modified for Debugging

1. `services/webapp-react/src/hooks/useDogDetails.js`
   - Added breakpoint checkpoint logs
   - Enhanced result inspection logging

2. `services/webapp-react/src/repositories/dogRepository.js`
   - Added breakpoint checkpoint before return
   - Enhanced return value logging

3. `services/webapp-react/src/pages/DogDetails.jsx`
   - Added hook state checkpoint log
   - Enhanced state inspection logging

---

## Next Steps After Breakpoint Session

Once you've run through the breakpoints and have the actual `result` object structure, share:
1. What `result` looks like when paused at line 41
2. Whether `setDog` is called
3. What React DevTools shows for the `dog` prop
4. Any unexpected values or structures

This will help pinpoint the exact issue in the data flow.

