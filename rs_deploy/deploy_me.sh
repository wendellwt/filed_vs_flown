#!/bin/bash -x

# new (Feb 12): after previous apps were DELETED, resurrected them as 200 and 201
# old (Jan 29): publish to TWO different app_id's

if [ $# -ne 1 ] ; then
    echo "arg is either 'prod' which is app 200 or 'test' which is app 201"
    echo "note: ../browser/vue.config.js contains the app_id; adjust as necessary"
    exit 1
fi

case "$1" in

  200|prod)

    # Published url (app_id=200) : http://172.26.21.40:3939/filed_vs_flown/
    #                            : http://172.26.21.40:3939/connect/#/apps/200

    APP_TITLE="filed_vs_flown"
    APP_ID=200
    rm -r rsconnect-python
    cp -r app_id_200_rsconnect-python rsconnect-python
    ;;

  201|test)

    # TESTING   url (app_id=201) : http://172.26.21.40:3939/content/201/
    #                            : http://172.26.21.40:3939/connect/#/apps/201

    APP_TITLE="test_filed_vs_flown"
    APP_ID=201
    rm -r rsconnect-python
    cp -r app_id_201_rsconnect-python rsconnect-python
    ;;

  *)
    echo $"Usage: $0 {prod|test|200|201}"
    exit 1
esac

# ======= fvf notes:

# problem 1: ../browser build puts app_id into index.html; watch out if app_id changes

# problem 2: not sure where to get location of cssi favicon, but this works
sed "s%cssi_star.png%/content/${APP_ID}/static/cssi_star.png%" static/index.html > templates/index.html

# problem 3: main d.b. python functions are over in ../analysis; copy them to a local
# dir now
cp ../analysis/fvf_by_artcc.py copied/
cp ../analysis/everything.py   copied/
cp ../analysis/get_paths.py    copied/
cp ../analysis/get_feb.py      copied/

# problem 4: npm build put files in static dir, rs deploy (or flask) want them in
# the template dir
STATIC_FILES=`find static/ -type f | grep -v index.html`

# ok, here goes...
echo rsconnect deploy api --title $APP_TITLE --server http://172.26.21.40:3939 --api-key OV9jvi1YVE6WPYnSi09tX6i4UJvlciJc . \
     copied/fvf_by_artcc.py \
     copied/everything.py \
     copied/get_paths.py \
     copied/get_feb.py \
     templates/index.html  $STATIC_FILES

