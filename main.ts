import { TwitterApi } from 'https://raw.githubusercontent.com/LuisMayo/deno_twitter_api/main/twitterApi.ts';
import Ask from 'https://deno.land/x/ask@1.0.5/mod.ts';
import { CommentList } from "./comment-list.ts";
import { CommentBridge } from "./comment-list-bridge.ts";

export interface Credentials {
    consumerApiKey: string,
    consumerApiSecret: string,
    accessToken: string,
    accessTokenSecret: string
}
let keys: Credentials;

// We get the credentials
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

let lastId = '0'; // Last notification ID

try {
    lastId = await Deno.readTextFile('./id.txt');
} catch (e) {
    lastId = '0';
}

// We instanciate the twitter API
let twitterApi = new TwitterApi(keys);
let twitterApi2 = new TwitterApi(keys, { apiVersion: '2' });
let ID: string = (await (await (twitterApi.get('account/verify_credentials.json'))).json()).id_str;
setInterval(processNotifications, 10000); // 20000



// We check notifications each X ms
async function processNotifications() {
    const response = (await twitterApi2.get('users/' + ID + '/mentions', { 'tweet.fields': 'referenced_tweets', since_id: lastId }));
    const mentions = await response.json();
    if (mentions.data && mentions.data.length > 0) {
        lastId = mentions.data[0].id;
        Deno.writeTextFile('./id.txt', lastId);
        // For each notification...
        for (const mention of mentions.data) {
            let pointer = mention.referenced_tweets?.find((val: any) => val.type === 'replied_to')?.id;
            if (pointer == null) { // I wasn't mentioned in a thread
                break;
            }
            const list: CommentList[] = [];
            do { // ... We extract the whole thread up to that point
                const data = (await (await twitterApi2.get('tweets/' + pointer, { 'tweet.fields': 'referenced_tweets', expansions: 'author_id' })).json());
                try { // Try catch in case there is a deleted tweet
                    pointer = data.data.referenced_tweets?.find((val: any) => val.type === 'replied_to')?.id;
                    list.unshift(data);
                } catch (e) {
                    pointer = null;
                }
            } while (pointer);
            // console.log(JSON.stringify(list));
            // We get all the users sorted by how common they are
            const users = new Map<string, {name: string, comments: number}>();
            for (const tweet of list) {
                if (!users.has(tweet.includes.users[0].id)) {
                    users.set(tweet.includes.users[0].id, {name: tweet.includes.users[0].name, comments: 1});
                } else {
                    users.get(tweet.includes.users[0].id)!.comments++;
                }
            }
            const mostCommon = Array.from(users.values()).sort((a, b) => b.comments - a.comments);
            const commonForBridge = mostCommon.map(user => user.name);

            // We prepare the comment list for the bridge
            const bridgeList: CommentBridge[] = list.map(comment => new CommentBridge(comment));
            Deno.run({cmd: ['python', 'bridge.py', JSON.stringify(commonForBridge), JSON.stringify(bridgeList)], stdout: 'inherit', stderr: 'inherit'});
        }
    }
}
