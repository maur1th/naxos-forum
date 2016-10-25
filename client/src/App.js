import React, { Component } from 'react'
import './App.css'

const thread = {
  slug: 'this-is-a-test',
  title: 'This is a test',
  category: {
    title: 'J\'ai envie de parler pour ne rien dire',
  },
  isSticky: true,
  personal: true,
}

const posts = [
  {
    id: "1",
    author: {
      username: 'louis2',
      logo: 'logo.jpg',
      quote: 'cot cot cot',
      date_joined: '2016-10-24T20:37:39.617Z',
    },
    content: 'wazup gros?! :gum:',
    created: '2016-10-24T20:37:39.617Z',
    modified: '2016-10-24T20:37:39.617Z',
  },
  {
    id: "2",
    author: {
      username: 'mozert',
      logo: 'logo.jpg',
      date_joined: '2016-10-24T20:37:39.617Z',
    },
    content: 'Benny B?',
    created: '2016-10-24T20:37:39.617Z',
    modified: '2016-10-24T20:37:39.617Z',
  }
]

const poll = null


class App extends Component {
  render() {
    return (
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-10 col-md-offset-1">
            <div style={{paddingTop: "8px"}} />
            <ThreadContainer />
          </div>
        </div>
      </div>
    )
  }
}

class ThreadContainer extends Component {
  render() {
    return (
      <div>
        <Title title={thread.title} type={poll ? 'Sondage' : 'Sujet'}/>
        <PostList posts={posts} />
      </div>
    )
  }
}

const Title = ({title, type}) => {
  return (
    <div>
      <div className="row no-pad">
        <div className="col-md-2 hidden-xs text-left post-header">
          <div className="post-header-content">Auteur</div>
        </div>
        <div className="col-md-10 post-header">
          <div className="post-header-content">{type} : {title}</div>
        </div>
      </div>
    </div>
  )
}

const PostList = ({posts}) => {

  const renderPost = ({id, author, content, created, modified}) => (
    <div>
      <div className="row" key={id}>
        <PostAuthor {...author} />
        <PostMessage {...{content, created, modified}} />
      </div>
      <hr style={{margin: '8px', borderTop: '0'}} />
    </div>
  )

  return (
    <div>
      {posts.map(renderPost)}
    </div>
  )
}

const PostAuthor = ({username, quote, logo, date_joined}) => {
  return (
    <div className="col-md-2 text-center hidden-xs post-author">
      <div className="post-author-content">
        <p className="username">{username}</p>
        {quote ? <p className="quote">{quote}</p> : null}
        {logo ? <p><img src={`./${logo}`} alt={`${username} logo`}/></p> : null}
        <p className="footer">depuis le {date_joined}</p>
      </div>
    </div>
  )
}

const PostMessage = ({content, created, modified}) => {
  return (
    <div className="col-md-10 post-message">
      {content}
    </div>
  )
}

export default App
