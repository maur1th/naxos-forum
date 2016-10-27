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
    content: `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla erat nulla, consequat non mattis in, commodo feugiat ligula. Etiam eros nunc, ullamcorper in metus sit amet, venenatis pretium ipsum. Aenean et enim nec ligula tincidunt gravida. Proin semper malesuada enim non dictum. Mauris vel semper velit. Sed lobortis purus sed risus bibendum, non interdum nisi euismod. Donec id ultricies augue. Sed eu nibh a dolor faucibus lobortis ut et erat. Donec pellentesque dui et mauris accumsan, ullamcorper eleifend magna eleifend. Maecenas scelerisque rhoncus sem, a congue ipsum. Nullam tincidunt mollis commodo. Phasellus et libero eget nisl cursus gravida id eu nunc. Nunc vehicula tristique volutpat. Nam eleifend ultricies orci eu vehicula. Cras vel congue elit. In nisl felis, fringilla eu libero sit amet, mollis convallis est. Sed hendrerit tincidunt diam nec ultrices. Suspendisse potenti. Nunc at pulvinar lectus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Vivamus congue posuere orci, non mattis libero laoreet at. Vivamus fringilla vulputate sapien, mattis finibus enim pretium id. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Etiam vitae vestibulum lorem. Pellentesque magna elit, cursus vitae tellus sed, aliquam viverra dolor. Aliquam erat volutpat. Phasellus quis hendrerit sapien. Nulla vulputate, nunc pellentesque efficitur fermentum, mauris magna aliquam est, ac viverra ipsum metus at dolor. Vestibulum at consequat dui. Curabitur sit amet rutrum ex, vitae pellentesque nisi. Nunc a mi vel diam volutpat egestas. Donec pretium faucibus eleifend. Quisque dictum lobortis nibh, vitae rhoncus purus molestie eu. Nulla laoreet augue erat, rutrum condimentum ex consequat a. Mauris interdum ligula ornare ex blandit, at rutrum tellus ultrices. Sed ultrices justo mattis metus hendrerit, ac egestas nisl facilisis. Pellentesque dapibus orci ligula, et malesuada velit rutrum et. Quisque eget urna lectus. Aenean blandit dapibus eros nec ultricies. Integer condimentum ultrices magna feugiat tempor. Donec a ornare sem. Pellentesque eu felis sed mi imperdiet congue eu ut lacus. Donec tempus eros blandit turpis condimentum, ac laoreet felis aliquam. Nam finibus ac metus ut fermentum. Nullam nec lacinia quam. Vestibulum maximus lobortis nisl vitae hendrerit. Duis ac justo et eros convallis fringilla quis sit amet lectus. Donec laoreet, mauris at pretium lacinia, magna massa malesuada est, non aliquet sapien odio ut odio. Cras at mauris elementum, varius mauris et, tempus nisl. Duis tempor nisi ultrices orci interdum hendrerit.`,
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
          <div className="col-lg-10 col-lg-offset-1">
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
      <div className="thread-container">
        <Title title={thread.title} type={poll ? 'Sondage' : 'Sujet'}/>
        <PostList posts={posts} />
      </div>
    )
  }
}

const Title = (props) => {
  return (
    <div className="thread-title">
      <div className="row">
        <div className="col-sm-2 hidden-xs left-side">
          <div className="content">Auteur</div>
        </div>
        <div className="col-sm-10">
          <div className="content">
            {props.type} : {props.title}
          </div>
        </div>
      </div>
      <hr />
    </div>
  )
}

const PostList = (props) => {

  const renderPost = ({id, author, content, created, modified}) => (
    <div>
      <div className="row" key={id}>
        <PostAuthor {...author} />
        <PostMessage {...{author, content, created, modified}} />
      </div>
      <hr />
    </div>
  )

  return (
    <div className="post-list">
      {props.posts.map(renderPost)}
    </div>
  )
}

const PostAuthor = (props) => {
  return (
    <div className="col-sm-2 hidden-xs text-center author left-side">
      <div className="frame">
        <p className="username">{props.username}</p>
        {props.quote ? <p className="quote">{props.quote}</p> : null}
        {props.logo ? (
          <p><img src={`./${props.logo}`} alt={`${props.username} logo`}/></p>
        ) : null}
        <p className="footer">depuis le {props.date_joined}</p>
      </div>
    </div>
  )
}

const PostMessage = (props) => {

  const Header = () => (
    <div className="header">
      <span className="hidden-xs">Posté le {props.created}</span>
      <span className="hidden-sm hidden-lg hidden-md">
        <span className="username">
          {props.author.username}
        </span> | Le {props.created}
      </span>
      <span> | </span>
      <a href="">Citer</a>
      <span> | </span>
      {props.canEdit ? (
        <span>
          <a href="">Modifier</a>
          <span> | </span>
        </span>
      ) : null}
      <a href=""><span className="glyphicon glyphicon-link"></span></a>
    </div>
  )

  return (
    <div className="col-sm-10 message">
      <div className="frame">
        <Header />
        <hr />
        <div className="content">{props.content}</div>
        <br />
        <p className="footer">— Modifié le {props.modified}</p>
      </div>
    </div>
  )
}

export default App
