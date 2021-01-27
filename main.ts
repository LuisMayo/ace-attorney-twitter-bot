import { TwitterApi } from 'https://raw.githubusercontent.com/LuisMayo/deno_twitter_api/main/twitterApi.ts';
import Ask from 'https://deno.land/x/ask@1.0.5/mod.ts';
import { CommentBridge } from "./comment-list-bridge.ts";
import { TweetObject } from "./tweet.ts";

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

let lastId: string | null; // Last notification ID

try {
    lastId = await Deno.readTextFile('./id.txt');
} catch (e) {
    lastId = null;
}

// We instanciate the twitter API
let twitterApi = new TwitterApi(keys);
setInterval(processNotifications, 10000); // 20000



// We check notifications each X ms
async function processNotifications() {
    const params = lastId ? { since_id: lastId } : undefined;
    const response = (await twitterApi.get('statuses/mentions_timeline.json', params));
    let mentions: TweetObject[] = await response.json();

    if (mentions && mentions.length > 0) {
        lastId = mentions[0].id_str;
        Deno.writeTextFile('./id.txt', lastId);

        // We clean the string and we filter out that we don't want
        mentions = mentions.filter(mention => mention.text.includes('render'));
        mentions = mentions.map(mention => {
            mention.text = mention.text.replaceAll(/^(@\S+) +/, '');
            mention.text = mention.text.replaceAll(/(https)\S*/, '');
            return mention;
        });
        // For each notification...
        for (const mention of mentions) {
            let pointer = mention.in_reply_to_status_id_str;
            if (pointer == null) { // I wasn't mentioned in a thread
                break;
            }
            const list: TweetObject[] = [];
            do { // ... We extract the whole thread up to that point
                const data: TweetObject = (await (await twitterApi.get('statuses/show/' + pointer + '.json')).json());
                pointer = data.in_reply_to_status_id_str;
                list.unshift(data);
            } while (pointer);
            // console.log(JSON.stringify(list));
            // We get all the users sorted by how common they are
            const users = new Map<string, {name: string, comments: number}>();
            for (const tweet of list) {
                if (!users.has(tweet.user.id_str)) {
                    users.set(tweet.user.id_str, {name: tweet.user.name, comments: 1});
                } else {
                    users.get(tweet.user.id_str)!.comments++;
                }
            }
            const mostCommon = Array.from(users.values()).sort((a, b) => b.comments - a.comments);
            const commonForBridge = mostCommon.map(user => user.name);

            // We prepare the comment list for the bridge
            const bridgeList: CommentBridge[] = list.map(comment => new CommentBridge(comment));
            const python = Deno.run({cmd: ['python', 'bridge.py', JSON.stringify(commonForBridge), JSON.stringify(bridgeList), mention.id_str + ".mp4"], stdout: 'inherit', stderr: 'inherit'});
            await python.status();
            const video = await Deno.readFile(mention.id_str + ".mp4");
        }
    }
}
