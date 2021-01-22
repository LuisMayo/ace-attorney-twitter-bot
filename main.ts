import { TwitterApi } from 'https://raw.githubusercontent.com/LuisMayo/deno_twitter_api/main/twitterApi.ts';
import Ask from 'https://deno.land/x/ask@1.0.5/mod.ts';

export interface Credentials {
    consumerApiKey: string,
    consumerApiSecret: string,
    accessToken: string,
    accessTokenSecret: string
}
let keys: Credentials;

try {
    keys = JSON.parse(await Deno.readTextFile('./keys.json'));
} catch (e) {
    const ask = new Ask();
    keys = await ask.prompt([
        {
            name: 'consumerApiKey',
            type: 'input',
            message: 'consumerApiKey:'
        },
        {
            name: 'consumerApiSecret',
            type: 'input',
            message: 'consumerApiSecret:'
        },
        {
            name: 'accessToken',
            type: 'input',
            message: 'accessToken:'
        },
        {
            name: 'accessTokenSecret',
            type: 'input',
            message: 'accessTokenSecret:'
        }
    ]) as Credentials;
    Deno.writeTextFileSync('./keys.json', JSON.stringify(keys));
}

let lastId = '0';

try {
    lastId = await Deno.readTextFile('./id.txt');
} catch (e) {
    lastId = '0';
}

let twitterApi = new TwitterApi(keys);
let twitterApi2 = new TwitterApi(keys, { apiVersion: '2' });
let ID: string = (await (await (twitterApi.get('account/verify_credentials.json'))).json()).id_str;
setInterval(processNotifications, 10000); // 20000



async function processNotifications() {
    const response = (await twitterApi2.get('users/' + ID + '/mentions', { 'tweet.fields': 'referenced_tweets', 'user.fields': 'username', since_id: lastId }));
    const mentions = await response.json();
    if (mentions.data && mentions.data.length > 0) {
        lastId = mentions.data[0].id;
        Deno.writeTextFile('./id.txt', lastId);
        for (const mention of mentions.data) {
            console.log('====================');
            let pointer = mention.referenced_tweets.find((val: any) => val.type === 'replied_to').id;
            const list = [mention];
            do {
                const data = (await (await twitterApi2.get('tweets/' + pointer, { 'tweet.fields': 'referenced_tweets', 'user.fields': 'username' })).json()).data;
                pointer = data.referenced_tweets?.find((val: any) => val.type === 'replied_to')?.id;
                list.unshift(data);
            } while (pointer);
            console.log(list);
        }
    }
}
