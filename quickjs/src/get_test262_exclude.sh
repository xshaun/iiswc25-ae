TEST262_DIR=test262/test
find "$TEST262_DIR" -type f > /tmp/list

while IFS= read -r t; do
    output=$(grep "$t" test262_exclude.txt)
    if [ $? -eq 0 ]; then
        printf '\n skip ===== %s =====\n' "$t"
        continue
    fi

    printf '\n===== %s =====\n' "$t"
    
    # ./build-cheribsd-morello-purecap/bin/run-test262 -t -m -T 3600000 -c ./test262.conf -f $t
    output=$(./build-cheribsd-morello-purecap/bin/run-test262 -c ./test262.conf -f $t 2>&1)
    exit_code=$?

    # Check if output contains "Error" or if the command failed
    if  echo "$output" | grep -q "Error"; then
        echo "$t" >> test262_exclude.txt
    fi
    if [ $exit_code -ne 0 ]; then
        echo "$t" >> test262_exclude.txt
    fi
done < /tmp/list