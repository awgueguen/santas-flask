clear

echo '--- starting script ---'
echo

python3 init_db.py

echo '>>> data cleaned'
echo

curl -d "last_name=test&first_name=Toto&login=login&password=password" -X POST localhost:5000/elves
curl -d "first_name=Toto&last_name=test&login=test&password=password&illegal=True" -X POST localhost:5000/elves

echo '>>> index'
curl localhost:5000/elves
echo '>>> show'
curl localhost:5000/elves/2

echo '>>> elf created'
echo

# curl localhost:5000/toys
# curl localhost:5000/toys/1

# curl -d "child_name=tashi&toy=Chess" -X POST localhost:5000/wishes
# curl -d "toy=Barbie&child_name=tashi" -X POST localhost:5000/wishes

# echo '>>> wishes created'
# echo

# curl -d "name=test&description=nowhere&price=3&category=Outdoor" -X POST localhost:5000/toys

# echo '>>> toy created'
# echo


# curl "localhost:5000/schedules?login=login&password=password"
# echo '>>> wish check'
# curl -X PUT localhost:5000/schedules/1/done
# echo '>>> wish update'
# curl "localhost:5000/schedules?login=login&password=password"

echo '--- script end ---'
