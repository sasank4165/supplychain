# Login Troubleshooting Guide

## Issue: "Invalid username or password" Error

If you're getting "Invalid username or password" errors, follow these steps:

### Step 1: Verify Users File Exists

On SageMaker, run:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
ls -la auth/users.json
```

You should see the file. If not, the file is missing.

### Step 2: Test Authentication

Run the test script:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
python scripts/test_login.py
```

This will test all demo credentials and show you which ones work.

### Step 3: Restart Streamlit

The app caches the AuthManager, so you need to restart Streamlit:

1. **Stop the current Streamlit process:**
   - Press `Ctrl+C` in the terminal where Streamlit is running
   - Or find and kill the process:
     ```bash
     pkill -f streamlit
     ```

2. **Start Streamlit again:**
   ```bash
   cd /home/ec2-user/SageMaker/supplychain/mvp
     streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```

3. **Clear your browser cache:**
   - Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Or use incognito/private browsing mode

### Step 4: Verify Demo Credentials

Try logging in with these exact credentials:

| Username | Password |
|----------|----------|
| `demo_warehouse` | `demo123` |
| `demo_field` | `demo123` |
| `demo_procurement` | `demo123` |
| `demo_admin` | `demo123` |

**Important:** 
- Username is case-sensitive
- No spaces before or after
- Password is exactly `demo123` (lowercase)

### Step 5: Check Users File Content

View the users file:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
cat auth/users.json
```

You should see 4 users with the password hash `$2b$12$yAd4lGHoV7SUH2p.T37ys.HcVzMjmTmSz8cV.Z6URmIa/77xoYoWS`

### Step 6: Check App Logs

Check the application logs for errors:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
tail -50 logs/app.log
```

Look for authentication-related errors.

### Step 7: Verify Configuration

Run the path verification script:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
python scripts/verify_paths.py
```

This will show you:
- Which users.json file is being used
- How many users are in the file
- List of all users

## Common Issues

### Issue: Wrong users.json file

**Symptom:** Users file exists but login still fails

**Solution:** The app might be loading from a different path. Check the logs or run `verify_paths.py` to see which file is being used.

### Issue: Empty users.json

**Symptom:** File exists but has no users

**Solution:** Copy from the correct file:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
cp auth/users.json.example auth/users.json
```

Or use the working file from your local machine.

### Issue: Corrupted password hash

**Symptom:** File has users but authentication always fails

**Solution:** Recreate users with the script:
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp
python scripts/create_user.py
```

### Issue: App not restarting properly

**Symptom:** Changes to users.json don't take effect

**Solution:** Force kill and restart:
```bash
# Kill all Streamlit processes
pkill -9 -f streamlit

# Wait a few seconds
sleep 3

# Start fresh
cd /home/ec2-user/SageMaker/supplychain/mvp
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Still Not Working?

If none of the above works, try this emergency fix:

1. **Backup current users.json:**
   ```bash
   cd /home/ec2-user/SageMaker/supplychain/mvp
   cp auth/users.json auth/users.json.backup
   ```

2. **Create fresh users.json with known-good data:**
   ```bash
   cat > auth/users.json << 'EOF'
{
  "users": [
    {
      "username": "demo_warehouse",
      "password_hash": "$2b$12$yAd4lGHoV7SUH2p.T37ys.HcVzMjmTmSz8cV.Z6URmIa/77xoYoWS",
      "personas": ["Warehouse Manager"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    },
    {
      "username": "demo_field",
      "password_hash": "$2b$12$yAd4lGHoV7SUH2p.T37ys.HcVzMjmTmSz8cV.Z6URmIa/77xoYoWS",
      "personas": ["Field Engineer"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    },
    {
      "username": "demo_procurement",
      "password_hash": "$2b$12$yAd4lGHoV7SUH2p.T37ys.HcVzMjmTmSz8cV.Z6URmIa/77xoYoWS",
      "personas": ["Procurement Specialist"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    },
    {
      "username": "demo_admin",
      "password_hash": "$2b$12$yAd4lGHoV7SUH2p.T37ys.HcVzMjmTmSz8cV.Z6URmIa/77xoYoWS",
      "personas": ["Warehouse Manager", "Field Engineer", "Procurement Specialist"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    }
  ]
}
EOF
   ```

3. **Restart Streamlit:**
   ```bash
   pkill -f streamlit
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```

4. **Test login again**

## Contact Support

If you're still having issues after trying all the above, provide:
- Output of `python scripts/test_login.py`
- Output of `python scripts/verify_paths.py`
- Last 50 lines of `logs/app.log`
- Content of `auth/users.json`
