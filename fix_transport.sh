#\!/bin/bash

# Branches that need fixing based on our scan
branches=(
  "full-weather-working"
  "http-transport"
  "proper-config"
  "simple-http"
  "test-case-2-simple"
  "test-case-4-naming-app-py"
  "test-case-4-naming-index-py"
  "test-case-5-deps-complex"
  "test-case-5-deps-minimal"
  "test-case-5-deps-standard"
)

echo "🔧 Fixing transport configuration in ${#branches[@]} branches..."

for branch in "${branches[@]}"; do
  echo ""
  echo "📝 Processing branch: $branch"
  
  # Checkout the branch
  git checkout $branch
  
  # Find and fix Python files with incorrect transport
  for pyfile in *.py; do
    if [ -f "$pyfile" ] && grep -q 'transport="shttp"' "$pyfile"; then
      echo "  Fixing $pyfile..."
      sed -i '' 's/transport="shttp"/transport="streamable-http"/g' "$pyfile"
    fi
  done
  
  # Check if changes were made
  if git diff --quiet; then
    echo "  ✅ No changes needed"
  else
    echo "  ✅ Fixed transport configuration"
    git add -A
    git commit -m "Fix: Update transport from shttp to streamable-http

- Fixed invalid transport configuration causing timeouts
- Using correct FastMCP transport: streamable-http
- Part of systematic fix across all branches"
    
    git push origin $branch
    echo "  ✅ Pushed to origin/$branch"
  fi
done

echo ""
echo "✅ All branches updated\!"
