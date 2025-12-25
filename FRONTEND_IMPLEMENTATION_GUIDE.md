# Frontend Implementation Guide - Boards Enhancement

## 必要な変更

### 1. frontend/src/pages/Boards.tsx

#### State更新 (line 30-36)
```typescript
const [newBoard, setNewBoard] = useState({
  board_id: 0,
  name: '',
  description: '',
  read_level: 0,
  write_level: 1,
  enforced_news: false,      // 追加
  operator_id: null as string | null,  // 追加
})
```

#### ユーザー一覧の取得 (line 46の後に追加)
```typescript
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: async () => {
    const response = await adminAPI.getUsers()
    return response.data
  },
})
```

#### テーブルヘッダー更新 (line 141-149)
```tsx
<TableHead>
  <TableRow>
    <TableCell>Board ID</TableCell>
    <TableCell>Name</TableCell>
    <TableCell>Description</TableCell>
    <TableCell>Operator</TableCell>         {/* 新規 */}
    <TableCell>Enforced News</TableCell>    {/* 新規 */}
    <TableCell>Read Level</TableCell>
    <TableCell>Write Level</TableCell>
    <TableCell>Status</TableCell>
    <TableCell>Actions</TableCell>
  </TableRow>
</TableHead>
```

#### テーブル本体更新 (line 153-179)
```tsx
{boards?.map((board: any) => (
  <TableRow key={board.board_id}>
    <TableCell>{board.board_id}</TableCell>
    <TableCell><strong>{board.name}</strong></TableCell>
    <TableCell>{board.description || '-'}</TableCell>
    <TableCell>{board.operator_id || '-'}</TableCell>  {/* 新規 */}
    <TableCell>  {/* 新規 */}
      {board.enforced_news ? (
        <Chip label="Yes" color="warning" size="small" />
      ) : (
        <Chip label="No" color="default" size="small" />
      )}
    </TableCell>
    {/* 既存のセル... */}
  </TableRow>
))}
```

#### ダイアログフォーム追加 (line 240の後)
```tsx
<Box sx={{ mt: 2 }}>
  <FormControlLabel
    control={
      <Checkbox
        checked={newBoard.enforced_news}
        onChange={(e) => setNewBoard({ ...newBoard, enforced_news: e.target.checked })}
      />
    }
    label="Enforced News (display on login)"
  />
</Box>

<FormControl fullWidth margin="normal">
  <InputLabel>Board Operator</InputLabel>
  <Select
    value={newBoard.operator_id || ''}
    onChange={(e) => setNewBoard({ ...newBoard, operator_id: e.target.value || null })}
  >
    <MenuItem value="">None</MenuItem>
    {users?.map((user: any) => (
      <MenuItem key={user.user_id} value={user.user_id}>
        {user.handle_name} ({user.user_id})
      </MenuItem>
    ))}
  </Select>
</FormControl>
```

#### リセット処理更新 (line 115)
```typescript
setNewBoard({
  board_id: 0,
  name: '',
  description: '',
  read_level: 0,
  write_level: 1,
  enforced_news: false,     // 追加
  operator_id: null,        // 追加
})
```

### 2. frontend/src/components/Layout.tsx

必要なインポートを追加：
```typescript
import { FormControlLabel, Checkbox, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
```

## 実装状況

✅ バックエンドAPI完成（新フィールド対応済み）
✅ データベースモデル完成
⚠️ フロントエンドUI（このガイドに従って実装）

## テスト手順

1. バックエンド起動
2. フロントエンド起動
3. 管理画面で掲示板作成
4. Enforced Newsをチェック
5. Operatorを選択
6. 保存して確認
